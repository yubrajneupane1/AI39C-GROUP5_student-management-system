-- ============================================================
--  Acadlytics – Full Database Schema (synced from live DB)
--  Safe to run on a fresh install. Use the ALTER section
--  at the bottom to upgrade an existing database safely.
-- ============================================================

CREATE DATABASE IF NOT EXISTS Acadlytics;
USE Acadlytics;

-- ── 1. users ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `users` (
  `id`       int          NOT NULL AUTO_INCREMENT,
  `fullname` varchar(100) DEFAULT NULL,
  `email`    varchar(100) DEFAULT NULL,
  `username` varchar(100) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `role`     varchar(20)  NOT NULL DEFAULT 'student',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ── 2. courses ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `courses` (
  `id`          int           NOT NULL AUTO_INCREMENT,
  `name`        varchar(100)  NOT NULL,
  `description` varchar(1000) DEFAULT NULL,
  `teacher_id`  int           DEFAULT NULL,
  `capacity`    int           DEFAULT 50,
  `created_at`  timestamp     NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ── 3. enrollments ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `enrollments` (
  `id`          int       NOT NULL AUTO_INCREMENT,
  `student_id`  int       NOT NULL,
  `course_id`   int       NOT NULL,
  `enrolled_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ── 4. attendance ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `attendance` (
  `id`         int                      NOT NULL AUTO_INCREMENT,
  `student_id` int                      NOT NULL,
  `course_id`  int                      NOT NULL,
  `date`       date                     NOT NULL,
  `status`     enum('present','absent') DEFAULT 'present',
  `marked_by`  int                      DEFAULT NULL,
  `created_at` timestamp                NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ── 5. marks ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `marks` (
  `id`         int           NOT NULL AUTO_INCREMENT,
  `student_id` int           NOT NULL,
  `course_id`  int           NOT NULL,
  `title`      varchar(100)  DEFAULT NULL,
  `score`      decimal(5,2)  DEFAULT NULL,
  `total`      decimal(5,2)  DEFAULT '100.00',
  `marked_by`  int           DEFAULT NULL,
  `created_at` timestamp     NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ── 6. fees ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `fees` (
  `id`          int                    NOT NULL AUTO_INCREMENT,
  `student_id`  int                    NOT NULL,
  `amount`      decimal(10,2)          NOT NULL,
  `description` varchar(255)           DEFAULT NULL,
  `status`      enum('paid','unpaid')  DEFAULT 'unpaid',
  `due_date`    date                   DEFAULT NULL,
  `paid_at`     timestamp              NULL DEFAULT NULL,
  `created_at`  timestamp              NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ── 7. resources ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `resources` (
  `id`          int           NOT NULL AUTO_INCREMENT,
  `course_id`   int           NOT NULL,
  `teacher_id`  int           NOT NULL,
  `title`       varchar(100)  NOT NULL,
  `description` text,
  `link`        varchar(2000) DEFAULT NULL,
  `created_at`  timestamp     NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ── 8. weeks ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `weeks` (
  `id`          int          NOT NULL AUTO_INCREMENT,
  `course_id`   int          NOT NULL,
  `week_number` int          NOT NULL,
  `title`       varchar(100) DEFAULT NULL,
  `created_at`  timestamp    NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ── 9. lessons ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `lessons` (
  `id`            int           NOT NULL AUTO_INCREMENT,
  `week_id`       int           NOT NULL,
  `lesson_number` int           NOT NULL,
  `title`         varchar(100)  NOT NULL,
  `content`       text,
  `module_link`   varchar(1000) DEFAULT NULL,
  `created_at`    timestamp     NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ── 10. tasks ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `tasks` (
  `id`                 int          NOT NULL AUTO_INCREMENT,
  `lesson_id`          int          NOT NULL,
  `title`              varchar(100) NOT NULL,
  `description`        text,
  `deadline`           datetime     DEFAULT NULL,
  `created_at`         timestamp    NULL DEFAULT CURRENT_TIMESTAMP,
  `course_id`          int          DEFAULT NULL,
  `week_id`            int          DEFAULT NULL,
  `teacher_id`         int          DEFAULT NULL,
  `time_limit_minutes` int          DEFAULT NULL,
  `due_date`           datetime     DEFAULT NULL,
  `submission_type`    varchar(20)  NOT NULL DEFAULT 'text',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ── 11. submissions ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `submissions` (
  `id`            int          NOT NULL AUTO_INCREMENT,
  `task_id`       int          NOT NULL,
  `student_id`    int          NOT NULL,
  `text_response` text,
  `file_path`     varchar(500) DEFAULT NULL,
  `submitted_at`  timestamp    NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ── 12. task_submissions ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS `task_submissions` (
  `id`           int                              NOT NULL AUTO_INCREMENT,
  `task_id`      int                              NOT NULL,
  `student_id`   int                              NOT NULL,
  `text_answer`  text,
  `file_url`     varchar(512)                     DEFAULT NULL,
  `status`       enum('submitted','late','graded') NOT NULL DEFAULT 'submitted',
  `grade`        decimal(5,2)                     DEFAULT NULL,
  `feedback`     text,
  `submitted_at` datetime                         DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_task_student` (`task_id`, `student_id`),
  KEY `student_id` (`student_id`),
  CONSTRAINT `task_submissions_ibfk_1` FOREIGN KEY (`task_id`)    REFERENCES `tasks` (`id`) ON DELETE CASCADE,
  CONSTRAINT `task_submissions_ibfk_2` FOREIGN KEY (`student_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ── 13. study_materials ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS `study_materials` (
  `id`            int                                    NOT NULL AUTO_INCREMENT,
  `course_id`     int                                    NOT NULL,
  `week_id`       int                                    DEFAULT NULL,
  `teacher_id`    int                                    NOT NULL,
  `material_type` enum('manual','file','link','video')   NOT NULL DEFAULT 'file',
  `title`         varchar(255)                           NOT NULL,
  `description`   text,
  `file_url`      varchar(512)                           DEFAULT NULL,
  `created_at`    datetime                               DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `course_id`  (`course_id`),
  KEY `week_id`    (`week_id`),
  KEY `teacher_id` (`teacher_id`),
  CONSTRAINT `study_materials_ibfk_1` FOREIGN KEY (`course_id`)  REFERENCES `courses` (`id`) ON DELETE CASCADE,
  CONSTRAINT `study_materials_ibfk_2` FOREIGN KEY (`week_id`)    REFERENCES `weeks`   (`id`) ON DELETE SET NULL,
  CONSTRAINT `study_materials_ibfk_3` FOREIGN KEY (`teacher_id`) REFERENCES `users`   (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ── 14. course_materials ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS `course_materials` (
  `id`        int          NOT NULL AUTO_INCREMENT,
  `course_id` int          NOT NULL,
  `week_no`   int          NOT NULL,
  `title`     varchar(255) NOT NULL,
  `link`      varchar(500) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `course_id` (`course_id`),
  CONSTRAINT `course_materials_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ── 15. lesson_resources ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS `lesson_resources` (
  `id`        int           NOT NULL AUTO_INCREMENT,
  `lesson_id` int           NOT NULL,
  `title`     varchar(100)  DEFAULT NULL,
  `link`      varchar(1000) DEFAULT NULL,
  `file_path` varchar(500)  DEFAULT NULL,
  `created_at` timestamp    NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ── 16. course_resources ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS `course_resources` (
  `id`          int          NOT NULL AUTO_INCREMENT,
  `course_id`   int          NOT NULL,
  `title`       varchar(255) NOT NULL,
  `description` text,
  PRIMARY KEY (`id`),
  KEY `course_id` (`course_id`),
  CONSTRAINT `course_resources_ibfk_1` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- ============================================================
--  DEFAULT SEED DATA
-- ============================================================

INSERT IGNORE INTO `users` (`id`, `fullname`, `email`, `username`, `password`, `role`) VALUES
(1, 'Yubraj Neupane Chhetri', 'yubraj@gmail.com',      'yubraj13',    'scrypt:32768:8:1$6z5Eq5omnffqWoTq$9f05f7e377a567e7367a6e4fedcf3dbeca52d7a79820e44e5ea2fc507d272aded64afeb08f829e98a9687b0aec29b4db534785d48221bb29106d7fceee94fb43', 'student'),
(2, 'Abishek Bimali',         'Abisheksir@gmail.com',  'Prof.Abishek', 'scrypt:32768:8:1$BR6S5SaUUe2UhwEd$a66d3608e0febde15403e65993c7278fa50e0942e6e96f775709813d82526b1ba572681c6f2e78aa06c3ee9289e11c8fd1952e9c2dfb5ec59c1f317ee2b043f2', 'admin'),
(3, 'shuvranjal shah',        'mango@gmail.com',       'shuvranjal',  'scrypt:32768:8:1$935PBUfH8rvw83lT$6baf3da199f78ff1695db13d4cd014c8c215274ba47fef7edcc2147168e03cd7133c73b0e1d8b7e4c309686250890e2691f2130c8bbaaa8a8694decf392c33d9', 'teacher'),
(5, 'riyush awal',            'riyush@gmial.com',      'riyush',      'scrypt:32768:8:1$dC0Ew5LmqqmEECCV$7c1d91b63f0e10676a9a070aa83f94311a24251eb003de2ff0cebadf966cb538a003fd9ddb0c1e1b14007efab5035cf9ee117465662e39f351822c7433a486bd', 'student'),
(6, 'Nischal Kunwar',         'aaijo@gmail.com',       'Nischal',     'scrypt:32768:8:1$w5Kosk93qeris6Wb$dda990dd931350fcbed830928cdce47f54bcc87839925b4c3c12bc78475176081afc669b900acd1e933eaffbf1891e94025970ee2760162ae1d3d8c34da8deb6', 'student'),
(7, 'Mubarak Rain',           'mubarak@gmail.com',     'Mubarak',     'scrypt:32768:8:1$sUkV6CC7oK4JgjC6$030e3e64af521d4f1f25512cb2e54e2d1629a9edad83821440b23cea9a4ff4351f39af7fe9d80bafad5fac4ee4140f9de46098f87b07d0c54bc277f907e309ae', 'teacher');

INSERT IGNORE INTO `courses` (`id`, `name`, `description`, `teacher_id`, `capacity`) VALUES
(4, 'ST505CMD-WORKING WITH DATA',          'This module introduces you to the world of data, by focusing on the theory and practice of database systems. It covers the uses of data in computer science and society, focusing on key legal, ethical, social and professional issues (LESPI), as well as technical topics including relational databases, normalization, querying, security, and simple data analysis using R and Python.  Learning Outcome', 4, 50),
(5, 'ST404-PROGRAMMING:PROFESSIONAL PRACTICE', 'Students will focus on new concepts for the exploration of different programming paradigms, particularly (but not limited to) procedural and object-oriented programming (OOP). They will also investigate the differences between major programming languages and be exposed to best practice design and development techniques for software.', 7, 50);

INSERT IGNORE INTO `enrollments` (`id`, `student_id`, `course_id`) VALUES
(4, 2, 4),
(5, 5, 4),
(6, 6, 4),
(7, 2, 5),
(8, 5, 5),
(9, 6, 5);


-- ============================================================
--  UPGRADE SCRIPT — run this on your EXISTING database to
--  sync it without losing any data. Safe to run multiple times.
-- ============================================================

-- courses: description was varchar(500), now varchar(1000)
ALTER TABLE `courses` MODIFY COLUMN `description` varchar(1000) DEFAULT NULL;

-- resources: link was varchar(1000), now varchar(2000)
ALTER TABLE `resources` MODIFY COLUMN `link` varchar(2000) DEFAULT NULL;
