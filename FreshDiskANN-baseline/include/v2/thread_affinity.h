#pragma once

#include <cstdlib>
#include <cstring>
#include <iostream>
#include <mutex>
#include <sstream>
#include <string>
#include <vector>

#ifndef _WINDOWS
#include <pthread.h>
#include <sched.h>
#include <unistd.h>
#endif

namespace diskann {
namespace thread_affinity {

static constexpr const char *kAffinityEnableEnv =
    "DISKANN_ENABLE_CPU_AFFINITY";
static constexpr const char *kAffinityAllowedCpusEnv =
    "DISKANN_CPU_AFFINITY_CPUS";
static constexpr const char *kSearchRoleCpusEnv = "DISKANN_SEARCH_CPUS";
static constexpr const char *kInsertRoleCpusEnv = "DISKANN_INSERT_CPUS";
static constexpr const char *kMergeRoleCpusEnv = "DISKANN_MERGE_CPUS";

#ifndef _WINDOWS
inline bool affinity_enabled() {
  const char *value = std::getenv(kAffinityEnableEnv);
  if (value == nullptr) {
    return false;
  }

  return std::strcmp(value, "0") != 0 &&
         std::strcmp(value, "false") != 0 &&
         std::strcmp(value, "FALSE") != 0;
}

inline std::vector<int> get_allowed_cpus() {
  cpu_set_t cpu_set;
  CPU_ZERO(&cpu_set);

  if (sched_getaffinity(0, sizeof(cpu_set), &cpu_set) != 0) {
    return {};
  }

  std::vector<int> cpus;
  for (int cpu = 0; cpu < CPU_SETSIZE; ++cpu) {
    if (CPU_ISSET(cpu, &cpu_set)) {
      cpus.push_back(cpu);
    }
  }
  return cpus;
}

inline std::vector<int> parse_cpu_list(const char *value) {
  std::vector<int> cpus;
  if (value == nullptr || *value == '\0') {
    return cpus;
  }

  std::stringstream stream(value);
  std::string token;
  while (std::getline(stream, token, ',')) {
    if (token.empty()) {
      continue;
    }

    const std::size_t dash = token.find('-');
    if (dash == std::string::npos) {
      cpus.push_back(std::stoi(token));
      continue;
    }

    const int begin = std::stoi(token.substr(0, dash));
    const int end = std::stoi(token.substr(dash + 1));
    if (begin <= end) {
      for (int cpu = begin; cpu <= end; ++cpu) {
        cpus.push_back(cpu);
      }
    } else {
      for (int cpu = begin; cpu >= end; --cpu) {
        cpus.push_back(cpu);
      }
    }
  }

  return cpus;
}

inline std::string format_cpu_list(const std::vector<int> &cpus) {
  std::ostringstream stream;
  for (std::size_t i = 0; i < cpus.size(); ++i) {
    if (i != 0) {
      stream << ",";
    }
    stream << cpus[i];
  }
  return stream.str();
}

inline std::vector<int> assign_role_cpus(const std::vector<int> &allowed_cpus,
                                         const std::size_t start_offset,
                                         const std::size_t thread_count) {
  std::vector<int> assigned_cpus;
  if (allowed_cpus.empty() || thread_count == 0) {
    return assigned_cpus;
  }

  assigned_cpus.reserve(thread_count);
  for (std::size_t i = 0; i < thread_count; ++i) {
    assigned_cpus.push_back(
        allowed_cpus[(start_offset + i) % allowed_cpus.size()]);
  }
  return assigned_cpus;
}

inline void configure_balanced_role_cpus(const std::size_t search_threads,
                                         const std::size_t insert_threads,
                                         const std::size_t merge_threads,
                                         const char *label) {
  std::vector<int> allowed_cpus =
      parse_cpu_list(std::getenv(kAffinityAllowedCpusEnv));
  if (allowed_cpus.empty()) {
    allowed_cpus = get_allowed_cpus();
  }

  if (allowed_cpus.empty()) {
    std::cerr << label
              << " could not determine any allowed CPUs. CPU affinity is "
                 "disabled."
              << std::endl;
    return;
  }

  const std::vector<int> search_cpus =
      assign_role_cpus(allowed_cpus, 0, search_threads);
  const std::vector<int> insert_cpus =
      assign_role_cpus(allowed_cpus, search_threads, insert_threads);
  const std::vector<int> merge_cpus = assign_role_cpus(
      allowed_cpus, search_threads + insert_threads, merge_threads);

  setenv(kAffinityEnableEnv, "1", 1);
  setenv(kSearchRoleCpusEnv, format_cpu_list(search_cpus).c_str(), 1);
  setenv(kInsertRoleCpusEnv, format_cpu_list(insert_cpus).c_str(), 1);
  setenv(kMergeRoleCpusEnv, format_cpu_list(merge_cpus).c_str(), 1);

  const std::size_t total_requested =
      search_threads + insert_threads + merge_threads;
  if (allowed_cpus.size() < total_requested) {
    std::cerr << label << " requested " << total_requested
              << " pinned threads, but only " << allowed_cpus.size()
              << " CPUs are available. Some CPUs will host multiple threads."
              << std::endl;
  }

  std::cerr << label << " enabled CPU affinity."
            << " allowed=" << format_cpu_list(allowed_cpus)
            << " search=" << format_cpu_list(search_cpus)
            << " insert=" << format_cpu_list(insert_cpus)
            << " merge=" << format_cpu_list(merge_cpus) << std::endl;
}

inline bool restrict_thread_to_cpus(const std::vector<int> &cpus,
                                    const char *role) {
  cpu_set_t cpu_set;
  CPU_ZERO(&cpu_set);
  bool has_valid_cpu = false;

  for (const int cpu : cpus) {
    if (cpu >= 0 && cpu < CPU_SETSIZE) {
      CPU_SET(cpu, &cpu_set);
      has_valid_cpu = true;
    }
  }

  if (!has_valid_cpu) {
    return false;
  }

  if (pthread_setaffinity_np(pthread_self(), sizeof(cpu_set), &cpu_set) != 0) {
    static std::once_flag warning_once;
    std::call_once(warning_once, [role, cpus]() {
      std::cerr << "Failed to restrict a " << role << " thread to CPUs "
                << format_cpu_list(cpus) << std::endl;
    });
    return false;
  }
  return true;
}

inline const std::vector<int> &search_role_cpus() {
  static const std::vector<int> cpus =
      parse_cpu_list(std::getenv(kSearchRoleCpusEnv));
  return cpus;
}

inline const std::vector<int> &insert_role_cpus() {
  static const std::vector<int> cpus =
      parse_cpu_list(std::getenv(kInsertRoleCpusEnv));
  return cpus;
}

inline const std::vector<int> &merge_role_cpus() {
  static const std::vector<int> cpus =
      parse_cpu_list(std::getenv(kMergeRoleCpusEnv));
  return cpus;
}

inline void pin_search_thread(const std::size_t) {
  if (!affinity_enabled()) {
    return;
  }

  const std::vector<int> &cpus = search_role_cpus();
  if (!cpus.empty()) {
    restrict_thread_to_cpus(cpus, "search");
  }
}

inline void pin_insert_thread(const std::size_t) {
  if (!affinity_enabled()) {
    return;
  }

  const std::vector<int> &cpus = insert_role_cpus();
  if (!cpus.empty()) {
    restrict_thread_to_cpus(cpus, "insert");
  }
}

inline void pin_merge_thread(const std::size_t) {
  if (!affinity_enabled()) {
    return;
  }

  const std::vector<int> &cpus = merge_role_cpus();
  if (!cpus.empty()) {
    restrict_thread_to_cpus(cpus, "merge");
  }
}
#else
inline void configure_balanced_role_cpus(const std::size_t, const std::size_t,
                                         const std::size_t, const char *) {}
inline void pin_search_thread(const std::size_t) {}
inline void pin_insert_thread(const std::size_t) {}
inline void pin_merge_thread(const std::size_t) {}
#endif

}  // namespace thread_affinity
}  // namespace diskann
