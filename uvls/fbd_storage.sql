-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Waktu pembuatan: 01 Des 2025 pada 17.12
-- Versi server: 10.4.32-MariaDB
-- Versi PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `fbd_storage`
--

-- --------------------------------------------------------

--
-- Struktur dari tabel `login`
--

CREATE TABLE `login` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `level` enum('Admin','UT1','UT2','GUEST') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `login`
--

INSERT INTO `login` (`id`, `username`, `password`, `level`) VALUES
(1, 'admin', 'admin', 'Admin'),
(2, 'ut1', 'ut1', 'UT1'),
(3, 'ut2', 'ut2', 'UT2'),
(4, 'guest', 'guest', 'GUEST');

-- --------------------------------------------------------

--
-- Struktur dari tabel `logsheet`
--

CREATE TABLE `logsheet` (
  `id` int(11) NOT NULL,
  `area` varchar(512) DEFAULT NULL,
  `procces` varchar(512) DEFAULT NULL,
  `item` varchar(512) DEFAULT NULL,
  `point` varchar(512) DEFAULT NULL,
  `min` int(11) DEFAULT NULL,
  `max` int(11) DEFAULT NULL,
  `unit` varchar(512) DEFAULT NULL,
  `freq` varchar(512) DEFAULT NULL,
  `shift_satu` int(11) DEFAULT NULL,
  `remarks_satu` varchar(512) DEFAULT NULL,
  `t_satu` timestamp NULL DEFAULT NULL,
  `shift_dua` int(11) DEFAULT NULL,
  `remarks_dua` varchar(512) DEFAULT NULL,
  `t_dua` timestamp NULL DEFAULT NULL,
  `shift_tiga` int(11) DEFAULT NULL,
  `remarks_tiga` varchar(512) DEFAULT NULL,
  `t_tiga` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `logsheet`
--

INSERT INTO `logsheet` (`id`, `area`, `procces`, `item`, `point`, `min`, `max`, `unit`, `freq`, `shift_satu`, `remarks_satu`, `t_satu`, `shift_dua`, `remarks_dua`, `t_dua`, `shift_tiga`, `remarks_tiga`, `t_tiga`) VALUES
(1, 'F-BD STORAGE', 'TK-101-1', 'Level', 'LT-1101', 4000, 18000, 'mm', 'once/8hrs', 4000, '', '2025-11-28 16:54:22', 8000, 'Strainer kotor', '2025-11-28 14:15:20', 8000, '', '2025-11-25 12:33:20'),
(2, 'F-BD STORAGE', 'TK-101-1', 'Level', 'LT-1102', 20, 80, '%', 'once/8hrs', 80, '', '2025-11-25 12:15:11', 0, '', NULL, 60, 'ok', '2025-11-25 13:47:47'),
(3, 'F-BD STORAGE', 'TK-101-1', 'Bottom temp', 'TG-1001', 3, 15, '°C', 'once/8hrs', 4, 'ok', '2025-11-25 12:40:22', 0, '', NULL, 3, 'Strainer kotor', '2025-11-25 13:50:13'),
(4, 'F-BD STORAGE', 'TK-101-1', 'Bottom Pressure', 'PG-1001', 0, 6, 'kg/cm²G', 'once/8hrs', 0, '', '2025-11-25 12:15:11', 0, '', NULL, 0, '', NULL),
(5, 'F-BD STORAGE', 'TK-101-2', 'Level', 'LT-1116', 4000, 18000, 'mm', 'once/8hrs', 0, '', '2025-11-25 12:15:11', 0, '', NULL, 0, '', NULL),
(6, 'F-BD STORAGE', 'TK-101-2', 'Level', 'LT-1117', 20, 80, '%', 'once/8hrs', 0, '', '2025-11-25 12:15:11', 0, '', NULL, 0, '', NULL),
(7, 'F-BD STORAGE', 'TK-101-2', 'Bottom temp', 'TG-1035', 3, 15, '°C', 'once/8hrs', 0, '', '2025-11-25 12:15:11', 0, '', NULL, 0, '', NULL),
(8, 'F-BD STORAGE', 'TK-101-2', 'Bottom Pressure', 'PG-1043', 0, 6, 'kg/cm²G', 'once/8hrs', 0, '', '2025-11-25 12:15:11', 0, '', NULL, 0, '', NULL),
(9, 'F-BD STORAGE', 'PU-101', 'Pressure', 'PG-1002', 8, 12, 'kg/cm²G', 'once/8hrs', 15, 'Level gauge tidak mau turun', '2025-11-27 17:20:47', 0, '', NULL, 0, '', NULL),
(10, 'F-BD STORAGE', 'PU-101', 'Pressure', 'PT-1103', 8, 12, 'kg/cm²G', 'once/8hrs', 0, '', '2025-11-25 12:15:11', 0, '', NULL, 0, '', NULL),
(11, 'F-BD STORAGE', 'HE-101', 'Level', 'LT-1103', 30, 50, '%', 'once/8hrs', 0, '', '2025-11-25 12:15:11', 0, '', NULL, 0, '', NULL),
(12, 'F-BD STORAGE', 'HE-101', 'Level', 'LG-1001', 30, 50, '%', 'once/8hrs', 0, '', '2025-11-25 12:15:11', 0, '', NULL, 0, '', NULL),
(13, 'F-BD STORAGE', 'HE-101', 'Nh3 temp', 'TG-1002', 0, 15, '°C', 'once/8hrs', 0, '', '2025-11-25 12:15:11', 0, '', NULL, 0, '', NULL),
(14, 'F-BD STORAGE', 'HE-101', 'BD temp', 'TG-1027', 0, 20, '°C', 'once/8hrs', 0, '', '2025-11-25 12:15:11', 0, '', NULL, 0, '', NULL),
(15, 'F-BD STORAGE', 'HE-101', 'DW temp', 'TG-1031', 10, 25, '°C', 'once/8hrs', 0, '', '2025-11-25 12:15:11', 0, '', NULL, 0, '', NULL),
(16, 'F-BD STORAGE', 'HE-101', 'Pressure', 'PT-1102', 3, 5, 'kg/cm²G', 'once/8hrs', 0, '', '2025-11-25 12:15:11', 0, '', NULL, 0, '', NULL),
(17, 'F-BD STORAGE', 'HE-101', 'Pressure', 'PG-1004', 3, 5, 'kg/cm²G', 'once/8hrs', 0, '', '2025-11-25 12:15:11', 0, '', NULL, 0, '', NULL),
(18, 'F-BD STORAGE', 'PU-103', 'Pressure', 'PG-1003', 2, 5, 'kg/cm²G', 'once/8hrs', 0, '', '2025-11-25 12:15:11', 0, '', NULL, 0, '', NULL),
(19, 'F-BD STORAGE', 'Line Unloading BD', 'Press Line', 'PG-Press Line', 0, 6, 'kg/cm²G', 'once/8hrs', 0, '', '2025-11-25 12:15:11', 0, '', NULL, 0, '', NULL),
(20, 'F-BD STORAGE', 'Line Unloading BD', 'Press Bott TK-1', 'PG-Press Bott TK-1', 0, 6, 'kg/cm²G', 'once/8hrs', 0, '', '2025-11-25 12:15:11', 0, '', NULL, 0, '', NULL),
(21, 'F-BD STORAGE', 'Line Unloading BD', 'Press Bott TK-2', 'PG-Press Bott TK-2', 0, 6, 'kg/cm²G', 'once/8hrs', 0, '', '2025-11-25 12:15:11', 0, '', NULL, 0, '', NULL);

-- --------------------------------------------------------

--
-- Struktur dari tabel `sheetsatu`
--

CREATE TABLE `sheetsatu` (
  `id` int(11) NOT NULL,
  `area` varchar(512) DEFAULT NULL,
  `procces` varchar(512) DEFAULT NULL,
  `item` varchar(512) DEFAULT NULL,
  `point` varchar(512) DEFAULT NULL,
  `tanggal` date DEFAULT NULL,
  `min` double DEFAULT NULL,
  `max` double DEFAULT NULL,
  `unit` varchar(512) DEFAULT NULL,
  `freq` varchar(512) DEFAULT NULL,
  `shift_satu` double DEFAULT NULL,
  `remarks_satu` varchar(512) DEFAULT NULL,
  `t_satu` timestamp NULL DEFAULT NULL,
  `shift_dua` double DEFAULT NULL,
  `remarks_dua` varchar(512) DEFAULT NULL,
  `t_dua` timestamp NULL DEFAULT NULL,
  `shift_tiga` double DEFAULT NULL,
  `remarks_tiga` varchar(512) DEFAULT NULL,
  `t_tiga` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data untuk tabel `sheetsatu`
--

INSERT INTO `sheetsatu` (`id`, `area`, `procces`, `item`, `point`, `tanggal`, `min`, `max`, `unit`, `freq`, `shift_satu`, `remarks_satu`, `t_satu`, `shift_dua`, `remarks_dua`, `t_dua`, `shift_tiga`, `remarks_tiga`, `t_tiga`) VALUES
(1, 'F-BD STORAGE', 'TK-101-1', 'Level', 'LT-1101', NULL, 4000, 18000, 'mm', 'once/8hrs', 0, '', NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(2, 'F-BD STORAGE', 'TK-101-1', 'Level', 'LT-1102', NULL, 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(3, 'F-BD STORAGE', 'TK-101-1', 'Bottom temp', 'TG-1001', NULL, 3, 15, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(4, 'F-BD STORAGE', 'TK-101-1', 'Bottom Pressure', 'PG-1001', NULL, 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(5, 'F-BD STORAGE', 'TK-101-2', 'Level', 'LT-1116', NULL, 4000, 18000, 'mm', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(6, 'F-BD STORAGE', 'TK-101-2', 'Level', 'LT-1117', NULL, 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(7, 'F-BD STORAGE', 'TK-101-2', 'Bottom temp', 'TG-1035', NULL, 3, 15, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(8, 'F-BD STORAGE', 'TK-101-2', 'Bottom Pressure', 'PG-1043', NULL, 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(9, 'F-BD STORAGE', 'PU-101', 'Operation Pump A/B', 'Operation Pump A', NULL, NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(10, 'F-BD STORAGE', 'PU-101', 'Pressure', 'PG-1002', NULL, 8, 12, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(11, 'F-BD STORAGE', 'PU-101', 'Pressure', 'PT-1103', NULL, 8, 12, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(12, 'F-BD STORAGE', 'HE-101', 'Level', 'LT-1103', NULL, 30, 50, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(13, 'F-BD STORAGE', 'HE-101', 'Level', 'LG-1001', NULL, 30, 50, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(14, 'F-BD STORAGE', 'HE-101', 'Nh3 temp', 'TG-1002', NULL, 0, 15, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(15, 'F-BD STORAGE', 'HE-101', 'BD temp', 'TG-1027', NULL, 0, 20, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(16, 'F-BD STORAGE', 'HE-101', 'DW temp', 'TG-1031', NULL, 10, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(17, 'F-BD STORAGE', 'HE-101', 'Pressure', 'PT-1102', NULL, 3, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(18, 'F-BD STORAGE', 'HE-101', 'Pressure', 'PG-1004', NULL, 3, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(19, 'F-BD STORAGE', 'PU-103', 'Operation Pump A/B', 'Operation Pump A', NULL, NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(20, 'F-BD STORAGE', 'PU-103', 'Pressure', 'PG-1003', NULL, 2, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(21, 'F-BD STORAGE', 'Line Unloading BD', 'Press Line', 'PG-Press Line', NULL, 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(22, 'F-BD STORAGE', 'Line Unloading BD', 'Press Bott TK-1', 'PG-Press Bot TK-1', NULL, 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(23, 'F-BD STORAGE', 'Line Unloading BD', 'Press Bott TK-2', 'PG-Press Bott TK-2', NULL, 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(24, 'R-BD STORAGE', 'TK-105-1', 'R-BD Level', 'LG-1002', NULL, 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(25, 'R-BD STORAGE', 'TK-105-1', 'Water Level', 'LT-1104', NULL, 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(26, 'R-BD STORAGE', 'TK-105-1', 'Water Level', 'LG-1003', NULL, 0, 70, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(27, 'R-BD STORAGE', 'TK-105-1', 'Temperature', 'TG-1003', NULL, 10, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(28, 'R-BD STORAGE', 'TK-105-1', 'Pressure', 'PG-1005', NULL, 1.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(29, 'R-BD STORAGE', 'TK-105-1', 'Pressure', 'PT-1104', NULL, 2.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(30, 'R-BD STORAGE', 'TK-105-2', 'R-BD Level', 'LG-1004', NULL, 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(31, 'R-BD STORAGE', 'TK-105-2', 'R-BD Level', 'LT-1105', NULL, 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(32, 'R-BD STORAGE', 'TK-105-2', 'Water Level', 'LG-1005', NULL, 0, 70, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(33, 'R-BD STORAGE', 'TK-105-2', 'Temperature', 'TG-1004', NULL, 10, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(34, 'R-BD STORAGE', 'TK-105-2', 'Pressure', 'PG-1006', NULL, 1.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(35, 'R-BD STORAGE', 'TK-105-2', 'Pressure', 'PT-1105', NULL, 1.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(36, 'R-BD STORAGE', 'PU-111', 'Operation Pump A/B', 'Operation Pump A', NULL, NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(37, 'R-BD STORAGE', 'PU-111', 'Pressure', 'PG-1107', NULL, 8, 11, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(38, 'R-BD STORAGE', 'PU-111', 'Pressure', 'PT-1106', NULL, 8, 11, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(39, 'TBC NAOH', 'DE-101', 'Level', 'LG-1006', NULL, 20, 60, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(40, 'TBC NAOH', 'DE-101', 'Temperature', 'TG-1005', NULL, 15, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(41, 'TBC NAOH', 'DE-101', 'Pressure', 'PG-1008', NULL, 5, 8, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(42, 'TBC NAOH', 'DE-101', 'Flow', 'FI-1001', NULL, 9, 11, 'm/H', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(43, 'TBC NAOH', 'PU-112', 'Operation Pump A/C', 'Operation Pump A', NULL, NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(44, 'TBC NAOH', 'PU-112', 'Pressure', 'PG-1012', NULL, 7, 10, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(45, 'TBC NAOH', 'DE-102', 'Level', 'LG-1007', NULL, 20, 60, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(46, 'TBC NAOH', 'DE-102', 'Temperature', 'TG-1006', NULL, 15, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(47, 'TBC NAOH', 'DE-102', 'Pressure', 'PG-1010', NULL, 5, 8, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(48, 'TBC NAOH', 'DE-102', 'Flow', 'FI1002', NULL, 9, 11, 'm/H', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(49, 'TBC NAOH', 'PU-112', 'Operation pump B/C', 'Operation Pump B', NULL, NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(50, 'TBC NAOH', 'PU-112', 'Pressure', 'PG-1012', NULL, 7, 10, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(51, 'TBC NAOH', 'TK-103', 'Level', 'LG-1008', NULL, 0, 70, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(52, 'TBC NAOH', 'TK-103', 'Temperature', 'TG-1007', NULL, 25, 35, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(53, 'TBC NAOH', 'TK-103', 'Pressure', 'PG-1013', NULL, 0, 1, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(54, 'SW & CW ', 'PU-815', 'Operation Pump A/B/C', '', NULL, NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(55, 'SW & CW ', 'PU-815', 'Disch Pressure', 'PG-Jetty', NULL, 3, 4.7, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(56, 'SW & CW ', 'PU-815', 'B/L Pressure', 'PG-8022', NULL, 2, 4.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(57, 'SW & CW ', 'TK-816', 'Level', 'LI-8104', NULL, 1, 1.6, 'x1000 mm', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(58, 'SW & CW ', 'PU-816', 'Disch Press (A)', 'PG-8105A', NULL, 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(59, 'SW & CW ', 'PU-816', 'Disch Press (B)', 'PG-8105B', NULL, 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(60, 'SW & CW ', 'PU-816', 'Disch Press (C)', 'PG-8105C', NULL, 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(61, 'SW & CW ', 'PU-816', 'Disch Press (D)', 'PG-8105D', NULL, 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(62, 'SW & CW ', 'HE-816A', 'CW temp outlet', 'TG-8004A', NULL, 30, 35, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(63, 'SW & CW ', 'HE-816A', 'SW temp outlet', 'TG=8005A', NULL, 32, 37, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(64, 'SW & CW ', 'HE-816A', 'CW temp outlet', 'PT-8106', NULL, 2.5, 4.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(65, 'SW & CW ', 'HE-861B', 'CW temp outlet', 'TG-8004B', NULL, 30, 35, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(66, 'SW & CW ', 'HE-861B', 'SW temp outlet', 'TG-8005B', NULL, 32, 37, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(67, 'SW & CW ', 'HE-861B', 'CW temp outlet', 'PG-8013', NULL, 2.5, 4.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(68, 'F-BD STORAGE', 'TK-101-1', 'Level', 'LT-1101', '2025-11-28', 4000, 18000, 'mm', 'once/8hrs', 12000, '', '2025-11-28 18:36:22', 9000, '', '2025-11-29 08:17:44', 8900, '', '2025-11-29 08:18:06'),
(69, 'F-BD STORAGE', 'TK-101-1', 'Level', 'LT-1102', '2025-11-28', 20, 80, '%', 'once/8hrs', 2, 'Strainer kotor', '2025-11-28 18:52:52', 30, '', '2025-11-29 08:38:04', 40, '', '2025-11-29 08:38:29'),
(70, 'F-BD STORAGE', 'TK-101-1', 'Bottom temp', 'TG-1001', '2025-11-28', 3, 15, '°C', 'once/8hrs', 50, 'Level gauge tidak mau turun', '2025-11-28 18:56:19', NULL, NULL, NULL, NULL, NULL, NULL),
(71, 'F-BD STORAGE', 'TK-101-1', 'Bottom Pressure', 'PG-1001', '2025-11-28', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(72, 'F-BD STORAGE', 'TK-101-2', 'Level', 'LT-1116', '2025-11-28', 4000, 18000, 'mm', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(73, 'F-BD STORAGE', 'TK-101-2', 'Level', 'LT-1117', '2025-11-28', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(74, 'F-BD STORAGE', 'TK-101-2', 'Bottom temp', 'TG-1035', '2025-11-28', 3, 15, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(75, 'F-BD STORAGE', 'TK-101-2', 'Bottom Pressure', 'PG-1043', '2025-11-28', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(76, 'F-BD STORAGE', 'PU-101', 'Operation Pump A/B', 'Opertaion Pump B', '2025-11-28', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(77, 'F-BD STORAGE', 'PU-101', 'Pressure', 'PG-1002', '2025-11-28', 8, 12, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(78, 'F-BD STORAGE', 'PU-101', 'Pressure', 'PT-1103', '2025-11-28', 8, 12, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(79, 'F-BD STORAGE', 'HE-101', 'Level', 'LT-1103', '2025-11-28', 30, 50, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(80, 'F-BD STORAGE', 'HE-101', 'Level', 'LG-1001', '2025-11-28', 30, 50, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(81, 'F-BD STORAGE', 'HE-101', 'Nh3 temp', 'TG-1002', '2025-11-28', 0, 15, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(82, 'F-BD STORAGE', 'HE-101', 'BD temp', 'TG-1027', '2025-11-28', 0, 20, '°C', 'once/8hrs', 15, '', '2025-11-28 18:11:02', NULL, NULL, NULL, NULL, NULL, NULL),
(83, 'F-BD STORAGE', 'HE-101', 'DW temp', 'TG-1031', '2025-11-28', 10, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(84, 'F-BD STORAGE', 'HE-101', 'Pressure', 'PT-1102', '2025-11-28', 3, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(85, 'F-BD STORAGE', 'HE-101', 'Pressure', 'PG-1004', '2025-11-28', 3, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(86, 'F-BD STORAGE', 'PU-103', 'Operation Pump A/B', 'Operation Pump B', '2025-11-28', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(87, 'F-BD STORAGE', 'PU-103', 'Pressure', 'PG-1003', '2025-11-28', 2, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(88, 'F-BD STORAGE', 'Line Unloading BD', 'Press Line', 'PG-Press Line', '2025-11-28', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(89, 'F-BD STORAGE', 'Line Unloading BD', 'Press Bott TK-1', 'PG-Press Bot TK-1', '2025-11-28', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(90, 'F-BD STORAGE', 'Line Unloading BD', 'Press Bott TK-2', 'PG-Press Bott TK-2', '2025-11-28', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(91, 'R-BD STORAGE', 'TK-105-1', 'R-BD Level', 'LG-1002', '2025-11-28', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(92, 'R-BD STORAGE', 'TK-105-1', 'Water Level', 'LT-1104', '2025-11-28', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(93, 'R-BD STORAGE', 'TK-105-1', 'Water Level', 'LG-1003', '2025-11-28', 0, 70, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(94, 'R-BD STORAGE', 'TK-105-1', 'Temperature', 'TG-1003', '2025-11-28', 10, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(95, 'R-BD STORAGE', 'TK-105-1', 'Pressure', 'PG-1005', '2025-11-28', 1.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(96, 'R-BD STORAGE', 'TK-105-1', 'Pressure', 'PT-1104', '2025-11-28', 2.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(97, 'R-BD STORAGE', 'TK-105-2', 'R-BD Level', 'LG-1004', '2025-11-28', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(98, 'R-BD STORAGE', 'TK-105-2', 'R-BD Level', 'LT-1105', '2025-11-28', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(99, 'R-BD STORAGE', 'TK-105-2', 'Water Level', 'LG-1005', '2025-11-28', 0, 70, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(100, 'R-BD STORAGE', 'TK-105-2', 'Temperature', 'TG-1004', '2025-11-28', 10, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(101, 'R-BD STORAGE', 'TK-105-2', 'Pressure', 'PG-1006', '2025-11-28', 1.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(102, 'R-BD STORAGE', 'TK-105-2', 'Pressure', 'PT-1105', '2025-11-28', 1.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(103, 'R-BD STORAGE', 'PU-111', 'Operation Pump A/B', '', '2025-11-28', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(104, 'R-BD STORAGE', 'PU-111', 'Pressure', 'PG-1107', '2025-11-28', 8, 11, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(105, 'R-BD STORAGE', 'PU-111', 'Pressure', 'PT-1106', '2025-11-28', 8, 11, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(106, 'TBC NAOH', 'DE-101', 'Level', 'LG-1006', '2025-11-28', 20, 60, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(107, 'TBC NAOH', 'DE-101', 'Temperature', 'TG-1005', '2025-11-28', 15, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(108, 'TBC NAOH', 'DE-101', 'Pressure', 'PG-1008', '2025-11-28', 5, 8, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(109, 'TBC NAOH', 'DE-101', 'Flow', 'FI-1001', '2025-11-28', 9, 11, 'm/H', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(110, 'TBC NAOH', 'PU-112', 'Operation Pump A/C', '', '2025-11-28', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(111, 'TBC NAOH', 'PU-112', 'Pressure', 'PG-1012', '2025-11-28', 7, 10, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(112, 'TBC NAOH', 'DE-102', 'Level', 'LG-1007', '2025-11-28', 20, 60, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(113, 'TBC NAOH', 'DE-102', 'Temperature', 'TG-1006', '2025-11-28', 15, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(114, 'TBC NAOH', 'DE-102', 'Pressure', 'PG-1010', '2025-11-28', 5, 8, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(115, 'TBC NAOH', 'DE-102', 'Flow', 'FI1002', '2025-11-28', 9, 11, 'm/H', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(116, 'TBC NAOH', 'PU-112', 'Operation pump B/C', '', '2025-11-28', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(117, 'TBC NAOH', 'PU-112', 'Pressure', 'PG-1012', '2025-11-28', 7, 10, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(118, 'TBC NAOH', 'TK-103', 'Level', 'LG-1008', '2025-11-28', 0, 70, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(119, 'TBC NAOH', 'TK-103', 'Temperature', 'TG-1007', '2025-11-28', 25, 35, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(120, 'TBC NAOH', 'TK-103', 'Pressure', 'PG-1013', '2025-11-28', 0, 1, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(121, 'SW & CW ', 'PU-815', 'Operation Pump A/B/C', '', '2025-11-28', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(122, 'SW & CW ', 'PU-815', 'Disch Pressure', 'PG-Jetty', '2025-11-28', 3, 4.7, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(123, 'SW & CW ', 'PU-815', 'B/L Pressure', 'PG-8022', '2025-11-28', 2, 4.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(124, 'SW & CW ', 'TK-816', 'Level', 'LI-8104', '2025-11-28', 1, 1.6, 'x1000 mm', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(125, 'SW & CW ', 'PU-816', 'Disch Press (A)', 'PG-8105A', '2025-11-28', 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(126, 'SW & CW ', 'PU-816', 'Disch Press (B)', 'PG-8105B', '2025-11-28', 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(127, 'SW & CW ', 'PU-816', 'Disch Press (C)', 'PG-8105C', '2025-11-28', 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(128, 'SW & CW ', 'PU-816', 'Disch Press (D)', 'PG-8105D', '2025-11-28', 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(129, 'SW & CW ', 'HE-816A', 'CW temp outlet', 'TG-8004A', '2025-11-28', 30, 35, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(130, 'SW & CW ', 'HE-816A', 'SW temp outlet', 'TG=8005A', '2025-11-28', 32, 37, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(131, 'SW & CW ', 'HE-816A', 'CW temp outlet', 'PT-8106', '2025-11-28', 2.5, 4.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(132, 'SW & CW ', 'HE-861B', 'CW temp outlet', 'TG-8004B', '2025-11-28', 30, 35, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(133, 'SW & CW ', 'HE-861B', 'SW temp outlet', 'TG-8005B', '2025-11-28', 32, 37, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(134, 'SW & CW ', 'HE-861B', 'CW temp outlet', 'PG-8013', '2025-11-28', 2.5, 4.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(195, 'F-BD STORAGE', 'TK-101-1', 'Level', 'LT-1101', '2025-11-29', 4000, 18000, 'mm', 'once/8hrs', 8500, '', '2025-11-28 18:34:38', 8000, '', '2025-11-29 08:09:10', 10000, '', '2025-11-29 08:12:55'),
(196, 'F-BD STORAGE', 'TK-101-1', 'Level', 'LT-1102', '2025-11-29', 20, 80, '%', 'once/8hrs', 50, '', '2025-11-29 08:38:57', 60, '', '2025-11-29 08:39:17', 70, '', '2025-11-29 08:39:36'),
(197, 'F-BD STORAGE', 'TK-101-1', 'Bottom temp', 'TG-1001', '2025-11-29', 3, 15, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(198, 'F-BD STORAGE', 'TK-101-1', 'Bottom Pressure', 'PG-1001', '2025-11-29', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(199, 'F-BD STORAGE', 'TK-101-2', 'Level', 'LT-1116', '2025-11-29', 4000, 18000, 'mm', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(200, 'F-BD STORAGE', 'TK-101-2', 'Level', 'LT-1117', '2025-11-29', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(201, 'F-BD STORAGE', 'TK-101-2', 'Bottom temp', 'TG-1035', '2025-11-29', 3, 15, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(202, 'F-BD STORAGE', 'TK-101-2', 'Bottom Pressure', 'PG-1043', '2025-11-29', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(203, 'F-BD STORAGE', 'PU-101', 'Operation Pump A/B', '', '2025-11-29', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(204, 'F-BD STORAGE', 'PU-101', 'Pressure', 'PG-1002', '2025-11-29', 8, 12, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(205, 'F-BD STORAGE', 'PU-101', 'Pressure', 'PT-1103', '2025-11-29', 8, 12, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(206, 'F-BD STORAGE', 'HE-101', 'Level', 'LT-1103', '2025-11-29', 30, 50, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(207, 'F-BD STORAGE', 'HE-101', 'Level', 'LG-1001', '2025-11-29', 30, 50, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(208, 'F-BD STORAGE', 'HE-101', 'Nh3 temp', 'TG-1002', '2025-11-29', 0, 15, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(209, 'F-BD STORAGE', 'HE-101', 'BD temp', 'TG-1027', '2025-11-29', 0, 20, '°C', 'once/8hrs', 13, '', '2025-11-28 18:11:29', NULL, NULL, NULL, NULL, NULL, NULL),
(210, 'F-BD STORAGE', 'HE-101', 'DW temp', 'TG-1031', '2025-11-29', 10, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(211, 'F-BD STORAGE', 'HE-101', 'Pressure', 'PT-1102', '2025-11-29', 3, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(212, 'F-BD STORAGE', 'HE-101', 'Pressure', 'PG-1004', '2025-11-29', 3, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(213, 'F-BD STORAGE', 'PU-103', 'Operation Pump A/B', '', '2025-11-29', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(214, 'F-BD STORAGE', 'PU-103', 'Pressure', 'PG-1003', '2025-11-29', 2, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(215, 'F-BD STORAGE', 'Line Unloading BD', 'Press Line', 'PG-Press Line', '2025-11-29', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(216, 'F-BD STORAGE', 'Line Unloading BD', 'Press Bott TK-1', 'PG-Press Bot TK-1', '2025-11-29', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(217, 'F-BD STORAGE', 'Line Unloading BD', 'Press Bott TK-2', 'PG-Press Bott TK-2', '2025-11-29', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(218, 'R-BD STORAGE', 'TK-105-1', 'R-BD Level', 'LG-1002', '2025-11-29', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(219, 'R-BD STORAGE', 'TK-105-1', 'Water Level', 'LT-1104', '2025-11-29', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(220, 'R-BD STORAGE', 'TK-105-1', 'Water Level', 'LG-1003', '2025-11-29', 0, 70, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(221, 'R-BD STORAGE', 'TK-105-1', 'Temperature', 'TG-1003', '2025-11-29', 10, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(222, 'R-BD STORAGE', 'TK-105-1', 'Pressure', 'PG-1005', '2025-11-29', 1.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(223, 'R-BD STORAGE', 'TK-105-1', 'Pressure', 'PT-1104', '2025-11-29', 2.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(224, 'R-BD STORAGE', 'TK-105-2', 'R-BD Level', 'LG-1004', '2025-11-29', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(225, 'R-BD STORAGE', 'TK-105-2', 'R-BD Level', 'LT-1105', '2025-11-29', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(226, 'R-BD STORAGE', 'TK-105-2', 'Water Level', 'LG-1005', '2025-11-29', 0, 70, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(227, 'R-BD STORAGE', 'TK-105-2', 'Temperature', 'TG-1004', '2025-11-29', 10, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(228, 'R-BD STORAGE', 'TK-105-2', 'Pressure', 'PG-1006', '2025-11-29', 1.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(229, 'R-BD STORAGE', 'TK-105-2', 'Pressure', 'PT-1105', '2025-11-29', 1.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(230, 'R-BD STORAGE', 'PU-111', 'Operation Pump A/B', '', '2025-11-29', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(231, 'R-BD STORAGE', 'PU-111', 'Pressure', 'PG-1107', '2025-11-29', 8, 11, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(232, 'R-BD STORAGE', 'PU-111', 'Pressure', 'PT-1106', '2025-11-29', 8, 11, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(233, 'TBC NAOH', 'DE-101', 'Level', 'LG-1006', '2025-11-29', 20, 60, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(234, 'TBC NAOH', 'DE-101', 'Temperature', 'TG-1005', '2025-11-29', 15, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(235, 'TBC NAOH', 'DE-101', 'Pressure', 'PG-1008', '2025-11-29', 5, 8, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(236, 'TBC NAOH', 'DE-101', 'Flow', 'FI-1001', '2025-11-29', 9, 11, 'm/H', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(237, 'TBC NAOH', 'PU-112', 'Operation Pump A/C', '', '2025-11-29', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(238, 'TBC NAOH', 'PU-112', 'Pressure', 'PG-1012', '2025-11-29', 7, 10, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(239, 'TBC NAOH', 'DE-102', 'Level', 'LG-1007', '2025-11-29', 20, 60, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(240, 'TBC NAOH', 'DE-102', 'Temperature', 'TG-1006', '2025-11-29', 15, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(241, 'TBC NAOH', 'DE-102', 'Pressure', 'PG-1010', '2025-11-29', 5, 8, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(242, 'TBC NAOH', 'DE-102', 'Flow', 'FI1002', '2025-11-29', 9, 11, 'm/H', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(243, 'TBC NAOH', 'PU-112', 'Operation pump B/C', '', '2025-11-29', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(244, 'TBC NAOH', 'PU-112', 'Pressure', 'PG-1012', '2025-11-29', 7, 10, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(245, 'TBC NAOH', 'TK-103', 'Level', 'LG-1008', '2025-11-29', 0, 70, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(246, 'TBC NAOH', 'TK-103', 'Temperature', 'TG-1007', '2025-11-29', 25, 35, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(247, 'TBC NAOH', 'TK-103', 'Pressure', 'PG-1013', '2025-11-29', 0, 1, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(248, 'SW & CW ', 'PU-815', 'Operation Pump A/B/C', '', '2025-11-29', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(249, 'SW & CW ', 'PU-815', 'Disch Pressure', 'PG-Jetty', '2025-11-29', 3, 4.7, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(250, 'SW & CW ', 'PU-815', 'B/L Pressure', 'PG-8022', '2025-11-29', 2, 4.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(251, 'SW & CW ', 'TK-816', 'Level', 'LI-8104', '2025-11-29', 1, 1.6, 'x1000 mm', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(252, 'SW & CW ', 'PU-816', 'Disch Press (A)', 'PG-8105A', '2025-11-29', 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(253, 'SW & CW ', 'PU-816', 'Disch Press (B)', 'PG-8105B', '2025-11-29', 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(254, 'SW & CW ', 'PU-816', 'Disch Press (C)', 'PG-8105C', '2025-11-29', 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(255, 'SW & CW ', 'PU-816', 'Disch Press (D)', 'PG-8105D', '2025-11-29', 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(256, 'SW & CW ', 'HE-816A', 'CW temp outlet', 'TG-8004A', '2025-11-29', 30, 35, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(257, 'SW & CW ', 'HE-816A', 'SW temp outlet', 'TG=8005A', '2025-11-29', 32, 37, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(258, 'SW & CW ', 'HE-816A', 'CW temp outlet', 'PT-8106', '2025-11-29', 2.5, 4.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(259, 'SW & CW ', 'HE-861B', 'CW temp outlet', 'TG-8004B', '2025-11-29', 30, 35, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(260, 'SW & CW ', 'HE-861B', 'SW temp outlet', 'TG-8005B', '2025-11-29', 32, 37, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(261, 'SW & CW ', 'HE-861B', 'CW temp outlet', 'PG-8013', '2025-11-29', 2.5, 4.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(322, 'F-BD STORAGE', 'TK-101-1', 'Level', 'LT-1101', '2025-11-27', 4000, 18000, 'mm', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(323, 'F-BD STORAGE', 'TK-101-1', 'Level', 'LT-1102', '2025-11-27', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(324, 'F-BD STORAGE', 'TK-101-1', 'Bottom temp', 'TG-1001', '2025-11-27', 3, 15, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(325, 'F-BD STORAGE', 'TK-101-1', 'Bottom Pressure', 'PG-1001', '2025-11-27', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(326, 'F-BD STORAGE', 'TK-101-2', 'Level', 'LT-1116', '2025-11-27', 4000, 18000, 'mm', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(327, 'F-BD STORAGE', 'TK-101-2', 'Level', 'LT-1117', '2025-11-27', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(328, 'F-BD STORAGE', 'TK-101-2', 'Bottom temp', 'TG-1035', '2025-11-27', 3, 15, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(329, 'F-BD STORAGE', 'TK-101-2', 'Bottom Pressure', 'PG-1043', '2025-11-27', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(330, 'F-BD STORAGE', 'PU-101', 'Operation Pump A/B', '', '2025-11-27', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(331, 'F-BD STORAGE', 'PU-101', 'Pressure', 'PG-1002', '2025-11-27', 8, 12, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(332, 'F-BD STORAGE', 'PU-101', 'Pressure', 'PT-1103', '2025-11-27', 8, 12, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(333, 'F-BD STORAGE', 'HE-101', 'Level', 'LT-1103', '2025-11-27', 30, 50, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(334, 'F-BD STORAGE', 'HE-101', 'Level', 'LG-1001', '2025-11-27', 30, 50, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(335, 'F-BD STORAGE', 'HE-101', 'Nh3 temp', 'TG-1002', '2025-11-27', 0, 15, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(336, 'F-BD STORAGE', 'HE-101', 'BD temp', 'TG-1027', '2025-11-27', 0, 20, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(337, 'F-BD STORAGE', 'HE-101', 'DW temp', 'TG-1031', '2025-11-27', 10, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(338, 'F-BD STORAGE', 'HE-101', 'Pressure', 'PT-1102', '2025-11-27', 3, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(339, 'F-BD STORAGE', 'HE-101', 'Pressure', 'PG-1004', '2025-11-27', 3, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(340, 'F-BD STORAGE', 'PU-103', 'Operation Pump A/B', '', '2025-11-27', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(341, 'F-BD STORAGE', 'PU-103', 'Pressure', 'PG-1003', '2025-11-27', 2, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(342, 'F-BD STORAGE', 'Line Unloading BD', 'Press Line', 'PG-Press Line', '2025-11-27', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(343, 'F-BD STORAGE', 'Line Unloading BD', 'Press Bott TK-1', 'PG-Press Bot TK-1', '2025-11-27', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(344, 'F-BD STORAGE', 'Line Unloading BD', 'Press Bott TK-2', 'PG-Press Bott TK-2', '2025-11-27', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(345, 'R-BD STORAGE', 'TK-105-1', 'R-BD Level', 'LG-1002', '2025-11-27', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(346, 'R-BD STORAGE', 'TK-105-1', 'Water Level', 'LT-1104', '2025-11-27', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(347, 'R-BD STORAGE', 'TK-105-1', 'Water Level', 'LG-1003', '2025-11-27', 0, 70, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(348, 'R-BD STORAGE', 'TK-105-1', 'Temperature', 'TG-1003', '2025-11-27', 10, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(349, 'R-BD STORAGE', 'TK-105-1', 'Pressure', 'PG-1005', '2025-11-27', 1.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(350, 'R-BD STORAGE', 'TK-105-1', 'Pressure', 'PT-1104', '2025-11-27', 2.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(351, 'R-BD STORAGE', 'TK-105-2', 'R-BD Level', 'LG-1004', '2025-11-27', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(352, 'R-BD STORAGE', 'TK-105-2', 'R-BD Level', 'LT-1105', '2025-11-27', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(353, 'R-BD STORAGE', 'TK-105-2', 'Water Level', 'LG-1005', '2025-11-27', 0, 70, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(354, 'R-BD STORAGE', 'TK-105-2', 'Temperature', 'TG-1004', '2025-11-27', 10, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(355, 'R-BD STORAGE', 'TK-105-2', 'Pressure', 'PG-1006', '2025-11-27', 1.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(356, 'R-BD STORAGE', 'TK-105-2', 'Pressure', 'PT-1105', '2025-11-27', 1.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(357, 'R-BD STORAGE', 'PU-111', 'Operation Pump A/B', '', '2025-11-27', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(358, 'R-BD STORAGE', 'PU-111', 'Pressure', 'PG-1107', '2025-11-27', 8, 11, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(359, 'R-BD STORAGE', 'PU-111', 'Pressure', 'PT-1106', '2025-11-27', 8, 11, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(360, 'TBC NAOH', 'DE-101', 'Level', 'LG-1006', '2025-11-27', 20, 60, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(361, 'TBC NAOH', 'DE-101', 'Temperature', 'TG-1005', '2025-11-27', 15, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(362, 'TBC NAOH', 'DE-101', 'Pressure', 'PG-1008', '2025-11-27', 5, 8, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(363, 'TBC NAOH', 'DE-101', 'Flow', 'FI-1001', '2025-11-27', 9, 11, 'm/H', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(364, 'TBC NAOH', 'PU-112', 'Operation Pump A/C', '', '2025-11-27', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(365, 'TBC NAOH', 'PU-112', 'Pressure', 'PG-1012', '2025-11-27', 7, 10, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(366, 'TBC NAOH', 'DE-102', 'Level', 'LG-1007', '2025-11-27', 20, 60, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(367, 'TBC NAOH', 'DE-102', 'Temperature', 'TG-1006', '2025-11-27', 15, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(368, 'TBC NAOH', 'DE-102', 'Pressure', 'PG-1010', '2025-11-27', 5, 8, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(369, 'TBC NAOH', 'DE-102', 'Flow', 'FI1002', '2025-11-27', 9, 11, 'm/H', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(370, 'TBC NAOH', 'PU-112', 'Operation pump B/C', '', '2025-11-27', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(371, 'TBC NAOH', 'PU-112', 'Pressure', 'PG-1012', '2025-11-27', 7, 10, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(372, 'TBC NAOH', 'TK-103', 'Level', 'LG-1008', '2025-11-27', 0, 70, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(373, 'TBC NAOH', 'TK-103', 'Temperature', 'TG-1007', '2025-11-27', 25, 35, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(374, 'TBC NAOH', 'TK-103', 'Pressure', 'PG-1013', '2025-11-27', 0, 1, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(375, 'SW & CW ', 'PU-815', 'Operation Pump A/B/C', '', '2025-11-27', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(376, 'SW & CW ', 'PU-815', 'Disch Pressure', 'PG-Jetty', '2025-11-27', 3, 4.7, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(377, 'SW & CW ', 'PU-815', 'B/L Pressure', 'PG-8022', '2025-11-27', 2, 4.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(378, 'SW & CW ', 'TK-816', 'Level', 'LI-8104', '2025-11-27', 1, 1.6, 'x1000 mm', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(379, 'SW & CW ', 'PU-816', 'Disch Press (A)', 'PG-8105A', '2025-11-27', 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(380, 'SW & CW ', 'PU-816', 'Disch Press (B)', 'PG-8105B', '2025-11-27', 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(381, 'SW & CW ', 'PU-816', 'Disch Press (C)', 'PG-8105C', '2025-11-27', 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(382, 'SW & CW ', 'PU-816', 'Disch Press (D)', 'PG-8105D', '2025-11-27', 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(383, 'SW & CW ', 'HE-816A', 'CW temp outlet', 'TG-8004A', '2025-11-27', 30, 35, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(384, 'SW & CW ', 'HE-816A', 'SW temp outlet', 'TG=8005A', '2025-11-27', 32, 37, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(385, 'SW & CW ', 'HE-816A', 'CW temp outlet', 'PT-8106', '2025-11-27', 2.5, 4.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(386, 'SW & CW ', 'HE-861B', 'CW temp outlet', 'TG-8004B', '2025-11-27', 30, 35, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(387, 'SW & CW ', 'HE-861B', 'SW temp outlet', 'TG-8005B', '2025-11-27', 32, 37, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(388, 'SW & CW ', 'HE-861B', 'CW temp outlet', 'PG-8013', '2025-11-27', 2.5, 4.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(449, 'F-BD STORAGE', 'TK-101-1', 'Level', 'LT-1101', '2025-11-30', 4000, 18000, 'mm', 'once/8hrs', 1999, '', '2025-11-30 12:32:09', 8500, '', '2025-11-29 08:14:51', 10000, '', '2025-11-29 08:13:28'),
(450, 'F-BD STORAGE', 'TK-101-1', 'Level', 'LT-1102', '2025-11-30', 20, 80, '%', 'once/8hrs', 30, '', '2025-11-29 08:43:09', 40, '', '2025-11-29 08:43:30', 25, '', '2025-11-29 08:43:42'),
(451, 'F-BD STORAGE', 'TK-101-1', 'Bottom temp', 'TG-1001', '2025-11-30', 3, 15, '°C', 'once/8hrs', 13, '', '2025-11-30 12:26:11', NULL, NULL, NULL, NULL, NULL, NULL),
(452, 'F-BD STORAGE', 'TK-101-1', 'Bottom Pressure', 'PG-1001', '2025-11-30', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(453, 'F-BD STORAGE', 'TK-101-2', 'Level', 'LT-1116', '2025-11-30', 4000, 18000, 'mm', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(454, 'F-BD STORAGE', 'TK-101-2', 'Level', 'LT-1117', '2025-11-30', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(455, 'F-BD STORAGE', 'TK-101-2', 'Bottom temp', 'TG-1035', '2025-11-30', 3, 15, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(456, 'F-BD STORAGE', 'TK-101-2', 'Bottom Pressure', 'PG-1043', '2025-11-30', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(457, 'F-BD STORAGE', 'PU-101', 'Operation Pump A/B', '', '2025-11-30', NULL, NULL, '', 'once/8hrs', 0, 'A', '2025-11-30 12:33:17', NULL, NULL, NULL, NULL, NULL, NULL),
(458, 'F-BD STORAGE', 'PU-101', 'Pressure', 'PG-1002', '2025-11-30', 8, 12, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(459, 'F-BD STORAGE', 'PU-101', 'Pressure', 'PT-1103', '2025-11-30', 8, 12, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(460, 'F-BD STORAGE', 'HE-101', 'Level', 'LT-1103', '2025-11-30', 30, 50, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(461, 'F-BD STORAGE', 'HE-101', 'Level', 'LG-1001', '2025-11-30', 30, 50, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(462, 'F-BD STORAGE', 'HE-101', 'Nh3 temp', 'TG-1002', '2025-11-30', 0, 15, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(463, 'F-BD STORAGE', 'HE-101', 'BD temp', 'TG-1027', '2025-11-30', 0, 20, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(464, 'F-BD STORAGE', 'HE-101', 'DW temp', 'TG-1031', '2025-11-30', 10, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(465, 'F-BD STORAGE', 'HE-101', 'Pressure', 'PT-1102', '2025-11-30', 3, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(466, 'F-BD STORAGE', 'HE-101', 'Pressure', 'PG-1004', '2025-11-30', 3, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(467, 'F-BD STORAGE', 'PU-103', 'Operation Pump A/B', '', '2025-11-30', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(468, 'F-BD STORAGE', 'PU-103', 'Pressure', 'PG-1003', '2025-11-30', 2, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(469, 'F-BD STORAGE', 'Line Unloading BD', 'Press Line', 'PG-Press Line', '2025-11-30', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(470, 'F-BD STORAGE', 'Line Unloading BD', 'Press Bott TK-1', 'PG-Press Bot TK-1', '2025-11-30', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(471, 'F-BD STORAGE', 'Line Unloading BD', 'Press Bott TK-2', 'PG-Press Bott TK-2', '2025-11-30', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(472, 'R-BD STORAGE', 'TK-105-1', 'R-BD Level', 'LG-1002', '2025-11-30', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(473, 'R-BD STORAGE', 'TK-105-1', 'Water Level', 'LT-1104', '2025-11-30', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(474, 'R-BD STORAGE', 'TK-105-1', 'Water Level', 'LG-1003', '2025-11-30', 0, 70, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(475, 'R-BD STORAGE', 'TK-105-1', 'Temperature', 'TG-1003', '2025-11-30', 10, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(476, 'R-BD STORAGE', 'TK-105-1', 'Pressure', 'PG-1005', '2025-11-30', 1.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(477, 'R-BD STORAGE', 'TK-105-1', 'Pressure', 'PT-1104', '2025-11-30', 2.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(478, 'R-BD STORAGE', 'TK-105-2', 'R-BD Level', 'LG-1004', '2025-11-30', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(479, 'R-BD STORAGE', 'TK-105-2', 'R-BD Level', 'LT-1105', '2025-11-30', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(480, 'R-BD STORAGE', 'TK-105-2', 'Water Level', 'LG-1005', '2025-11-30', 0, 70, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(481, 'R-BD STORAGE', 'TK-105-2', 'Temperature', 'TG-1004', '2025-11-30', 10, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(482, 'R-BD STORAGE', 'TK-105-2', 'Pressure', 'PG-1006', '2025-11-30', 1.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(483, 'R-BD STORAGE', 'TK-105-2', 'Pressure', 'PT-1105', '2025-11-30', 1.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(484, 'R-BD STORAGE', 'PU-111', 'Operation Pump A/B', '', '2025-11-30', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(485, 'R-BD STORAGE', 'PU-111', 'Pressure', 'PG-1107', '2025-11-30', 8, 11, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(486, 'R-BD STORAGE', 'PU-111', 'Pressure', 'PT-1106', '2025-11-30', 8, 11, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(487, 'TBC NAOH', 'DE-101', 'Level', 'LG-1006', '2025-11-30', 20, 60, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(488, 'TBC NAOH', 'DE-101', 'Temperature', 'TG-1005', '2025-11-30', 15, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(489, 'TBC NAOH', 'DE-101', 'Pressure', 'PG-1008', '2025-11-30', 5, 8, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(490, 'TBC NAOH', 'DE-101', 'Flow', 'FI-1001', '2025-11-30', 9, 11, 'm/H', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(491, 'TBC NAOH', 'PU-112', 'Operation Pump A/C', '', '2025-11-30', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(492, 'TBC NAOH', 'PU-112', 'Pressure', 'PG-1012', '2025-11-30', 7, 10, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(493, 'TBC NAOH', 'DE-102', 'Level', 'LG-1007', '2025-11-30', 20, 60, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(494, 'TBC NAOH', 'DE-102', 'Temperature', 'TG-1006', '2025-11-30', 15, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(495, 'TBC NAOH', 'DE-102', 'Pressure', 'PG-1010', '2025-11-30', 5, 8, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(496, 'TBC NAOH', 'DE-102', 'Flow', 'FI1002', '2025-11-30', 9, 11, 'm/H', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(497, 'TBC NAOH', 'PU-112', 'Operation pump B/C', '', '2025-11-30', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(498, 'TBC NAOH', 'PU-112', 'Pressure', 'PG-1012', '2025-11-30', 7, 10, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(499, 'TBC NAOH', 'TK-103', 'Level', 'LG-1008', '2025-11-30', 0, 70, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(500, 'TBC NAOH', 'TK-103', 'Temperature', 'TG-1007', '2025-11-30', 25, 35, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(501, 'TBC NAOH', 'TK-103', 'Pressure', 'PG-1013', '2025-11-30', 0, 1, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(502, 'SW & CW ', 'PU-815', 'Operation Pump A/B/C', '', '2025-11-30', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(503, 'SW & CW ', 'PU-815', 'Disch Pressure', 'PG-Jetty', '2025-11-30', 3, 4.7, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(504, 'SW & CW ', 'PU-815', 'B/L Pressure', 'PG-8022', '2025-11-30', 2, 4.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(505, 'SW & CW ', 'TK-816', 'Level', 'LI-8104', '2025-11-30', 1, 1.6, 'x1000 mm', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(506, 'SW & CW ', 'PU-816', 'Disch Press (A)', 'PG-8105A', '2025-11-30', 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(507, 'SW & CW ', 'PU-816', 'Disch Press (B)', 'PG-8105B', '2025-11-30', 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO `sheetsatu` (`id`, `area`, `procces`, `item`, `point`, `tanggal`, `min`, `max`, `unit`, `freq`, `shift_satu`, `remarks_satu`, `t_satu`, `shift_dua`, `remarks_dua`, `t_dua`, `shift_tiga`, `remarks_tiga`, `t_tiga`) VALUES
(508, 'SW & CW ', 'PU-816', 'Disch Press (C)', 'PG-8105C', '2025-11-30', 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(509, 'SW & CW ', 'PU-816', 'Disch Press (D)', 'PG-8105D', '2025-11-30', 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(510, 'SW & CW ', 'HE-816A', 'CW temp outlet', 'TG-8004A', '2025-11-30', 30, 35, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(511, 'SW & CW ', 'HE-816A', 'SW temp outlet', 'TG=8005A', '2025-11-30', 32, 37, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(512, 'SW & CW ', 'HE-816A', 'CW temp outlet', 'PT-8106', '2025-11-30', 2.5, 4.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(513, 'SW & CW ', 'HE-861B', 'CW temp outlet', 'TG-8004B', '2025-11-30', 30, 35, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(514, 'SW & CW ', 'HE-861B', 'SW temp outlet', 'TG-8005B', '2025-11-30', 32, 37, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(515, 'SW & CW ', 'HE-861B', 'CW temp outlet', 'PG-8013', '2025-11-30', 2.5, 4.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(576, 'F-BD STORAGE', 'TK-101-1', 'Level', 'LT-1101', '2025-12-01', 4000, 18000, 'mm', 'once/8hrs', 300, '', '2025-12-01 16:08:19', NULL, NULL, NULL, NULL, NULL, NULL),
(577, 'F-BD STORAGE', 'TK-101-1', 'Level', 'LT-1102', '2025-12-01', 20, 80, '%', 'once/8hrs', 35, '', '2025-12-01 14:40:36', 50, '', '2025-11-29 08:44:16', 55, '', '2025-11-29 08:44:30'),
(578, 'F-BD STORAGE', 'TK-101-1', 'Bottom temp', 'TG-1001', '2025-12-01', 3, 15, '°C', 'once/8hrs', 11, '', '2025-12-01 14:41:03', NULL, NULL, NULL, NULL, NULL, NULL),
(579, 'F-BD STORAGE', 'TK-101-1', 'Bottom Pressure', 'PG-1001', '2025-12-01', 0, 6, 'kg/cm²g', 'once/8hrs', 4.5, '', '2025-12-01 14:41:14', NULL, NULL, NULL, NULL, NULL, NULL),
(580, 'F-BD STORAGE', 'TK-101-2', 'Level', 'LT-1116', '2025-12-01', 4000, 18000, 'mm', 'once/8hrs', 4315, '', '2025-12-01 14:41:37', NULL, NULL, NULL, NULL, NULL, NULL),
(581, 'F-BD STORAGE', 'TK-101-2', 'Level', 'LT-1117', '2025-12-01', 20, 80, '%', 'once/8hrs', 45, '', '2025-12-01 14:42:12', NULL, NULL, NULL, NULL, NULL, NULL),
(582, 'F-BD STORAGE', 'TK-101-2', 'Bottom temp', 'TG-1035', '2025-12-01', 3, 15, '°C', 'once/8hrs', 15, 'Suara pompa kasar', '2025-12-01 14:54:21', NULL, NULL, NULL, NULL, NULL, NULL),
(583, 'F-BD STORAGE', 'TK-101-2', 'Bottom Pressure', 'PG-1043', '2025-12-01', 0, 6, 'kg/cm²g', 'once/8hrs', 6.5, '', '2025-12-01 14:54:37', NULL, NULL, NULL, NULL, NULL, NULL),
(584, 'F-BD STORAGE', 'PU-101', 'Operation Pump A/B', '', '2025-12-01', NULL, NULL, '', 'once/8hrs', 1, 'A', '2025-12-01 14:54:48', NULL, NULL, NULL, NULL, NULL, NULL),
(585, 'F-BD STORAGE', 'PU-101', 'Pressure', 'PG-1002', '2025-12-01', 8, 12, 'kg/cm²g', 'once/8hrs', 10, '', '2025-12-01 14:55:03', NULL, NULL, NULL, NULL, NULL, NULL),
(586, 'F-BD STORAGE', 'PU-101', 'Pressure', 'PT-1103', '2025-12-01', 8, 12, 'kg/cm²g', 'once/8hrs', 47, '', '2025-12-01 14:55:49', NULL, NULL, NULL, NULL, NULL, NULL),
(587, 'F-BD STORAGE', 'HE-101', 'Level', 'LT-1103', '2025-12-01', 30, 50, '%', 'once/8hrs', 15, '', '2025-12-01 14:56:19', NULL, NULL, NULL, NULL, NULL, NULL),
(588, 'F-BD STORAGE', 'HE-101', 'Level', 'LG-1001', '2025-12-01', 30, 50, '%', 'once/8hrs', 40, '', '2025-12-01 15:02:16', NULL, NULL, NULL, NULL, NULL, NULL),
(589, 'F-BD STORAGE', 'HE-101', 'Nh3 temp', 'TG-1002', '2025-12-01', 0, 15, '°C', 'once/8hrs', 7, '', '2025-12-01 15:02:24', NULL, NULL, NULL, NULL, NULL, NULL),
(590, 'F-BD STORAGE', 'HE-101', 'BD temp', 'TG-1027', '2025-12-01', 0, 20, '°C', 'once/8hrs', 15, '', '2025-12-01 15:02:33', NULL, NULL, NULL, NULL, NULL, NULL),
(591, 'F-BD STORAGE', 'HE-101', 'DW temp', 'TG-1031', '2025-12-01', 10, 25, '°C', 'once/8hrs', 16, '', '2025-12-01 15:02:46', NULL, NULL, NULL, NULL, NULL, NULL),
(592, 'F-BD STORAGE', 'HE-101', 'Pressure', 'PT-1102', '2025-12-01', 3, 5, 'kg/cm²g', 'once/8hrs', 4, '', '2025-12-01 15:03:16', NULL, NULL, NULL, NULL, NULL, NULL),
(593, 'F-BD STORAGE', 'HE-101', 'Pressure', 'PG-1004', '2025-12-01', 3, 5, 'kg/cm²g', 'once/8hrs', 4.5, '', '2025-12-01 15:03:28', NULL, NULL, NULL, NULL, NULL, NULL),
(594, 'F-BD STORAGE', 'PU-103', 'Operation Pump A/B', '', '2025-12-01', NULL, NULL, '', 'once/8hrs', 1, 'B', '2025-12-01 15:03:39', NULL, NULL, NULL, NULL, NULL, NULL),
(595, 'F-BD STORAGE', 'PU-103', 'Pressure', 'PG-1003', '2025-12-01', 2, 5, 'kg/cm²g', 'once/8hrs', 3, '', '2025-12-01 15:08:07', NULL, NULL, NULL, NULL, NULL, NULL),
(596, 'F-BD STORAGE', 'Line Unloading BD', 'Press Line', 'PG-Press Line', '2025-12-01', 0, 6, 'kg/cm²g', 'once/8hrs', 5, '', '2025-12-01 15:08:37', NULL, NULL, NULL, NULL, NULL, NULL),
(597, 'F-BD STORAGE', 'Line Unloading BD', 'Press Bott TK-1', 'PG-Press Bot TK-1', '2025-12-01', 0, 6, 'kg/cm²g', 'once/8hrs', 5, '', '2025-12-01 15:08:43', NULL, NULL, NULL, NULL, NULL, NULL),
(598, 'F-BD STORAGE', 'Line Unloading BD', 'Press Bott TK-2', 'PG-Press Bott TK-2', '2025-12-01', 0, 6, 'kg/cm²g', 'once/8hrs', 4.9, '', '2025-12-01 15:08:50', NULL, NULL, NULL, NULL, NULL, NULL),
(599, 'R-BD STORAGE', 'TK-105-1', 'R-BD Level', 'LG-1002', '2025-12-01', 20, 80, '%', 'once/8hrs', 45, '', '2025-12-01 15:08:57', NULL, NULL, NULL, NULL, NULL, NULL),
(600, 'R-BD STORAGE', 'TK-105-1', 'Water Level', 'LT-1104', '2025-12-01', 20, 80, '%', 'once/8hrs', 70, '', '2025-12-01 15:09:03', NULL, NULL, NULL, NULL, NULL, NULL),
(601, 'R-BD STORAGE', 'TK-105-1', 'Water Level', 'LG-1003', '2025-12-01', 0, 70, '%', 'once/8hrs', 60, '', '2025-12-01 15:16:03', NULL, NULL, NULL, NULL, NULL, NULL),
(602, 'R-BD STORAGE', 'TK-105-1', 'Temperature', 'TG-1003', '2025-12-01', 10, 25, '°C', 'once/8hrs', 20, '', '2025-12-01 15:16:17', NULL, NULL, NULL, NULL, NULL, NULL),
(603, 'R-BD STORAGE', 'TK-105-1', 'Pressure', 'PG-1005', '2025-12-01', 1.5, 3.5, 'kg/cm²g', 'once/8hrs', 2, '', '2025-12-01 15:16:51', NULL, NULL, NULL, NULL, NULL, NULL),
(604, 'R-BD STORAGE', 'TK-105-1', 'Pressure', 'PT-1104', '2025-12-01', 2.5, 3.5, 'kg/cm²g', 'once/8hrs', 2, '', '2025-12-01 15:17:02', NULL, NULL, NULL, NULL, NULL, NULL),
(605, 'R-BD STORAGE', 'TK-105-2', 'R-BD Level', 'LG-1004', '2025-12-01', 20, 80, '%', 'once/8hrs', 35, '', '2025-12-01 15:17:16', NULL, NULL, NULL, NULL, NULL, NULL),
(606, 'R-BD STORAGE', 'TK-105-2', 'R-BD Level', 'LT-1105', '2025-12-01', 20, 80, '%', 'once/8hrs', 40, '', '2025-12-01 15:17:26', NULL, NULL, NULL, NULL, NULL, NULL),
(607, 'R-BD STORAGE', 'TK-105-2', 'Water Level', 'LG-1005', '2025-12-01', 0, 70, '%', 'once/8hrs', 3, '', '2025-12-01 15:18:01', NULL, NULL, NULL, NULL, NULL, NULL),
(608, 'R-BD STORAGE', 'TK-105-2', 'Temperature', 'TG-1004', '2025-12-01', 10, 25, '°C', 'once/8hrs', 2, '', '2025-12-01 15:18:12', NULL, NULL, NULL, NULL, NULL, NULL),
(609, 'R-BD STORAGE', 'TK-105-2', 'Pressure', 'PG-1006', '2025-12-01', 1.5, 3.5, 'kg/cm²g', 'once/8hrs', 2, '', '2025-12-01 15:17:50', NULL, NULL, NULL, NULL, NULL, NULL),
(610, 'R-BD STORAGE', 'TK-105-2', 'Pressure', 'PT-1105', '2025-12-01', 1.5, 3.5, 'kg/cm²g', 'once/8hrs', 3, '', '2025-12-01 15:22:01', NULL, NULL, NULL, NULL, NULL, NULL),
(611, 'R-BD STORAGE', 'PU-111', 'Operation Pump A/B', '', '2025-12-01', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(612, 'R-BD STORAGE', 'PU-111', 'Pressure', 'PG-1107', '2025-12-01', 8, 11, 'kg/cm²g', 'once/8hrs', 9, '', '2025-12-01 15:27:13', NULL, NULL, NULL, NULL, NULL, NULL),
(613, 'R-BD STORAGE', 'PU-111', 'Pressure', 'PT-1106', '2025-12-01', 8, 11, 'kg/cm²g', 'once/8hrs', 8, '', '2025-12-01 15:28:34', NULL, NULL, NULL, NULL, NULL, NULL),
(614, 'TBC NAOH', 'DE-101', 'Level', 'LG-1006', '2025-12-01', 20, 60, '%', 'once/8hrs', 40, '', '2025-12-01 15:29:18', NULL, NULL, NULL, NULL, NULL, NULL),
(615, 'TBC NAOH', 'DE-101', 'Temperature', 'TG-1005', '2025-12-01', 15, 25, '°C', 'once/8hrs', 30, '', '2025-12-01 15:29:45', NULL, NULL, NULL, NULL, NULL, NULL),
(616, 'TBC NAOH', 'DE-101', 'Pressure', 'PG-1008', '2025-12-01', 5, 8, 'kg/cm²g', 'once/8hrs', 65, '', '2025-12-01 15:31:01', NULL, NULL, NULL, NULL, NULL, NULL),
(617, 'TBC NAOH', 'DE-101', 'Flow', 'FI-1001', '2025-12-01', 9, 11, 'm/H', 'once/8hrs', 10, '', '2025-12-01 15:39:08', NULL, NULL, NULL, NULL, NULL, NULL),
(618, 'TBC NAOH', 'PU-112', 'Operation Pump A/C', '', '2025-12-01', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(619, 'TBC NAOH', 'PU-112', 'Pressure', 'PG-1012', '2025-12-01', 7, 10, 'kg/cm²g', 'once/8hrs', 9, '', '2025-12-01 15:40:01', NULL, NULL, NULL, NULL, NULL, NULL),
(620, 'TBC NAOH', 'DE-102', 'Level', 'LG-1007', '2025-12-01', 20, 60, '%', 'once/8hrs', 55, '', '2025-12-01 15:50:29', NULL, NULL, NULL, NULL, NULL, NULL),
(621, 'TBC NAOH', 'DE-102', 'Temperature', 'TG-1006', '2025-12-01', 15, 25, '°C', 'once/8hrs', 20, '', '2025-12-01 15:40:45', NULL, NULL, NULL, NULL, NULL, NULL),
(622, 'TBC NAOH', 'DE-102', 'Pressure', 'PG-1010', '2025-12-01', 5, 8, 'kg/cm²g', 'once/8hrs', 7, '', '2025-12-01 15:40:59', NULL, NULL, NULL, NULL, NULL, NULL),
(623, 'TBC NAOH', 'DE-102', 'Flow', 'FI1002', '2025-12-01', 9, 11, 'm/H', 'once/8hrs', 10, '', '2025-12-01 15:41:26', NULL, NULL, NULL, NULL, NULL, NULL),
(624, 'TBC NAOH', 'PU-112', 'Operation pump B/C', '', '2025-12-01', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(625, 'TBC NAOH', 'PU-112', 'Pressure', 'PG-1012', '2025-12-01', 7, 10, '%', 'once/8hrs', 10, '', '2025-12-01 15:42:54', NULL, NULL, NULL, NULL, NULL, NULL),
(626, 'TBC NAOH', 'TK-103', 'Level', 'LG-1008', '2025-12-01', 0, 70, '%', 'once/8hrs', 50, '', '2025-12-01 15:50:44', NULL, NULL, NULL, NULL, NULL, NULL),
(627, 'TBC NAOH', 'TK-103', 'Temperature', 'TG-1007', '2025-12-01', 25, 35, '°C', 'once/8hrs', 35, '', '2025-12-01 15:50:53', NULL, NULL, NULL, NULL, NULL, NULL),
(628, 'TBC NAOH', 'TK-103', 'Pressure', 'PG-1013', '2025-12-01', 0, 1, 'kg/cm²g', 'once/8hrs', 4.5, '', '2025-12-01 15:51:02', NULL, NULL, NULL, NULL, NULL, NULL),
(629, 'SW & CW ', 'PU-815', 'Operation Pump A/B/C', '', '2025-12-01', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(630, 'SW & CW ', 'PU-815', 'Disch Pressure', 'PG-Jetty', '2025-12-01', 3, 4.7, 'kg/cm²g', 'once/8hrs', 4, '', '2025-12-01 15:51:09', NULL, NULL, NULL, NULL, NULL, NULL),
(631, 'SW & CW ', 'PU-815', 'B/L Pressure', 'PG-8022', '2025-12-01', 2, 4.5, 'kg/cm²g', 'once/8hrs', 3, '', '2025-12-01 15:51:16', NULL, NULL, NULL, NULL, NULL, NULL),
(632, 'SW & CW ', 'TK-816', 'Level', 'LI-8104', '2025-12-01', 1, 1.6, 'x1000 mm', 'once/8hrs', 2, '', '2025-12-01 15:51:44', NULL, NULL, NULL, NULL, NULL, NULL),
(633, 'SW & CW ', 'PU-816', 'Disch Press (A)', 'PG-8105A', '2025-12-01', 3.5, 5, 'kg/cm²g', 'once/8hrs', 4, '', '2025-12-01 15:51:56', NULL, NULL, NULL, NULL, NULL, NULL),
(634, 'SW & CW ', 'PU-816', 'Disch Press (B)', 'PG-8105B', '2025-12-01', 3.5, 5, 'kg/cm²g', 'once/8hrs', 4, '', '2025-12-01 15:52:27', NULL, NULL, NULL, NULL, NULL, NULL),
(635, 'SW & CW ', 'PU-816', 'Disch Press (C)', 'PG-8105C', '2025-12-01', 3.5, 5, 'kg/cm²g', 'once/8hrs', 0, 'stop', '2025-12-01 15:52:55', NULL, NULL, NULL, NULL, NULL, NULL),
(636, 'SW & CW ', 'PU-816', 'Disch Press (D)', 'PG-8105D', '2025-12-01', 3.5, 5, 'kg/cm²g', 'once/8hrs', 0, 'stop', '2025-12-01 15:53:05', NULL, NULL, NULL, NULL, NULL, NULL),
(637, 'SW & CW ', 'HE-816A', 'CW temp outlet', 'TG-8004A', '2025-12-01', 30, 35, '°C', 'once/8hrs', 30, '', '2025-12-01 15:56:44', NULL, NULL, NULL, NULL, NULL, NULL),
(638, 'SW & CW ', 'HE-816A', 'SW temp outlet', 'TG=8005A', '2025-12-01', 32, 37, '°C', 'once/8hrs', 33, '', '2025-12-01 15:57:37', NULL, NULL, NULL, NULL, NULL, NULL),
(639, 'SW & CW ', 'HE-816A', 'CW temp outlet', 'PT-8106', '2025-12-01', 2.5, 4.5, 'kg/cm²g', 'once/8hrs', 3, '', '2025-12-01 15:57:48', NULL, NULL, NULL, NULL, NULL, NULL),
(640, 'SW & CW ', 'HE-861B', 'CW temp outlet', 'TG-8004B', '2025-12-01', 30, 35, '°C', 'once/8hrs', 31, '', '2025-12-01 15:57:56', NULL, NULL, NULL, NULL, NULL, NULL),
(641, 'SW & CW ', 'HE-861B', 'SW temp outlet', 'TG-8005B', '2025-12-01', 32, 37, '°C', 'once/8hrs', 37, '', '2025-12-01 15:58:06', NULL, NULL, NULL, NULL, NULL, NULL),
(642, 'SW & CW ', 'HE-861B', 'CW temp outlet', 'PG-8013', '2025-12-01', 2.5, 4.5, 'kg/cm²g', 'once/8hrs', 3, '', '2025-12-01 15:58:15', NULL, NULL, NULL, NULL, NULL, NULL),
(703, 'F-BD STORAGE', 'TK-101-1', 'Level', 'LT-1101', '2025-12-02', 4000, 18000, 'mm', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(704, 'F-BD STORAGE', 'TK-101-1', 'Level', 'LT-1102', '2025-12-02', 20, 80, '%', 'once/8hrs', 35, '', '2025-11-29 08:50:27', 65, '', '2025-11-29 08:45:02', 75, '', '2025-11-29 08:45:17'),
(705, 'F-BD STORAGE', 'TK-101-1', 'Bottom temp', 'TG-1001', '2025-12-02', 3, 15, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(706, 'F-BD STORAGE', 'TK-101-1', 'Bottom Pressure', 'PG-1001', '2025-12-02', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(707, 'F-BD STORAGE', 'TK-101-2', 'Level', 'LT-1116', '2025-12-02', 4000, 18000, 'mm', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(708, 'F-BD STORAGE', 'TK-101-2', 'Level', 'LT-1117', '2025-12-02', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(709, 'F-BD STORAGE', 'TK-101-2', 'Bottom temp', 'TG-1035', '2025-12-02', 3, 15, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(710, 'F-BD STORAGE', 'TK-101-2', 'Bottom Pressure', 'PG-1043', '2025-12-02', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(711, 'F-BD STORAGE', 'PU-101', 'Operation Pump A/B', '', '2025-12-02', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(712, 'F-BD STORAGE', 'PU-101', 'Pressure', 'PG-1002', '2025-12-02', 8, 12, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(713, 'F-BD STORAGE', 'PU-101', 'Pressure', 'PT-1103', '2025-12-02', 8, 12, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(714, 'F-BD STORAGE', 'HE-101', 'Level', 'LT-1103', '2025-12-02', 30, 50, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(715, 'F-BD STORAGE', 'HE-101', 'Level', 'LG-1001', '2025-12-02', 30, 50, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(716, 'F-BD STORAGE', 'HE-101', 'Nh3 temp', 'TG-1002', '2025-12-02', 0, 15, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(717, 'F-BD STORAGE', 'HE-101', 'BD temp', 'TG-1027', '2025-12-02', 0, 20, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(718, 'F-BD STORAGE', 'HE-101', 'DW temp', 'TG-1031', '2025-12-02', 10, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(719, 'F-BD STORAGE', 'HE-101', 'Pressure', 'PT-1102', '2025-12-02', 3, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(720, 'F-BD STORAGE', 'HE-101', 'Pressure', 'PG-1004', '2025-12-02', 3, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(721, 'F-BD STORAGE', 'PU-103', 'Operation Pump A/B', '', '2025-12-02', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(722, 'F-BD STORAGE', 'PU-103', 'Pressure', 'PG-1003', '2025-12-02', 2, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(723, 'F-BD STORAGE', 'Line Unloading BD', 'Press Line', 'PG-Press Line', '2025-12-02', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(724, 'F-BD STORAGE', 'Line Unloading BD', 'Press Bott TK-1', 'PG-Press Bot TK-1', '2025-12-02', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(725, 'F-BD STORAGE', 'Line Unloading BD', 'Press Bott TK-2', 'PG-Press Bott TK-2', '2025-12-02', 0, 6, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(726, 'R-BD STORAGE', 'TK-105-1', 'R-BD Level', 'LG-1002', '2025-12-02', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(727, 'R-BD STORAGE', 'TK-105-1', 'Water Level', 'LT-1104', '2025-12-02', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(728, 'R-BD STORAGE', 'TK-105-1', 'Water Level', 'LG-1003', '2025-12-02', 0, 70, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(729, 'R-BD STORAGE', 'TK-105-1', 'Temperature', 'TG-1003', '2025-12-02', 10, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(730, 'R-BD STORAGE', 'TK-105-1', 'Pressure', 'PG-1005', '2025-12-02', 1.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(731, 'R-BD STORAGE', 'TK-105-1', 'Pressure', 'PT-1104', '2025-12-02', 2.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(732, 'R-BD STORAGE', 'TK-105-2', 'R-BD Level', 'LG-1004', '2025-12-02', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(733, 'R-BD STORAGE', 'TK-105-2', 'R-BD Level', 'LT-1105', '2025-12-02', 20, 80, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(734, 'R-BD STORAGE', 'TK-105-2', 'Water Level', 'LG-1005', '2025-12-02', 0, 70, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(735, 'R-BD STORAGE', 'TK-105-2', 'Temperature', 'TG-1004', '2025-12-02', 10, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(736, 'R-BD STORAGE', 'TK-105-2', 'Pressure', 'PG-1006', '2025-12-02', 1.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(737, 'R-BD STORAGE', 'TK-105-2', 'Pressure', 'PT-1105', '2025-12-02', 1.5, 3.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(738, 'R-BD STORAGE', 'PU-111', 'Operation Pump A/B', '', '2025-12-02', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(739, 'R-BD STORAGE', 'PU-111', 'Pressure', 'PG-1107', '2025-12-02', 8, 11, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(740, 'R-BD STORAGE', 'PU-111', 'Pressure', 'PT-1106', '2025-12-02', 8, 11, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(741, 'TBC NAOH', 'DE-101', 'Level', 'LG-1006', '2025-12-02', 20, 60, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(742, 'TBC NAOH', 'DE-101', 'Temperature', 'TG-1005', '2025-12-02', 15, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(743, 'TBC NAOH', 'DE-101', 'Pressure', 'PG-1008', '2025-12-02', 5, 8, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(744, 'TBC NAOH', 'DE-101', 'Flow', 'FI-1001', '2025-12-02', 9, 11, 'm/H', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(745, 'TBC NAOH', 'PU-112', 'Operation Pump A/C', '', '2025-12-02', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(746, 'TBC NAOH', 'PU-112', 'Pressure', 'PG-1012', '2025-12-02', 7, 10, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(747, 'TBC NAOH', 'DE-102', 'Level', 'LG-1007', '2025-12-02', 20, 60, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(748, 'TBC NAOH', 'DE-102', 'Temperature', 'TG-1006', '2025-12-02', 15, 25, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(749, 'TBC NAOH', 'DE-102', 'Pressure', 'PG-1010', '2025-12-02', 5, 8, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(750, 'TBC NAOH', 'DE-102', 'Flow', 'FI1002', '2025-12-02', 9, 11, 'm/H', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(751, 'TBC NAOH', 'PU-112', 'Operation pump B/C', 'Operation Pump C', '2025-12-02', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(752, 'TBC NAOH', 'PU-112', 'Pressure', 'PG-1012', '2025-12-02', 7, 10, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(753, 'TBC NAOH', 'TK-103', 'Level', 'LG-1008', '2025-12-02', 0, 70, '%', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(754, 'TBC NAOH', 'TK-103', 'Temperature', 'TG-1007', '2025-12-02', 25, 35, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(755, 'TBC NAOH', 'TK-103', 'Pressure', 'PG-1013', '2025-12-02', 0, 1, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(756, 'SW & CW ', 'PU-815', 'Operation Pump A/B/C', 'Operation Pump A', '2025-12-02', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(757, 'SW & CW ', 'PU-815', 'Disch Pressure', 'PG-Jetty', '2025-12-02', 3, 4.7, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(758, 'SW & CW ', 'PU-815', 'B/L Pressure', 'PG-8022', '2025-12-02', 2, 4.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(759, 'SW & CW ', 'TK-816', 'Level', 'LI-8104', '2025-12-02', 1, 1.6, 'x1000 mm', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(760, 'SW & CW ', 'PU-816', 'Disch Press (A)', 'PG-8105A', '2025-12-02', 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(761, 'SW & CW ', 'PU-816', 'Disch Press (B)', 'PG-8105B', '2025-12-02', 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(762, 'SW & CW ', 'PU-816', 'Disch Press (C)', 'PG-8105C', '2025-12-02', 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(763, 'SW & CW ', 'PU-816', 'Disch Press (D)', 'PG-8105D', '2025-12-02', 3.5, 5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(764, 'SW & CW ', 'HE-816A', 'CW temp outlet', 'TG-8004A', '2025-12-02', 30, 35, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(765, 'SW & CW ', 'HE-816A', 'SW temp outlet', 'TG=8005A', '2025-12-02', 32, 37, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(766, 'SW & CW ', 'HE-816A', 'CW temp outlet', 'PT-8106', '2025-12-02', 2.5, 4.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(767, 'SW & CW ', 'HE-861B', 'CW temp outlet', 'TG-8004B', '2025-12-02', 30, 35, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(768, 'SW & CW ', 'HE-861B', 'SW temp outlet', 'TG-8005B', '2025-12-02', 32, 37, '°C', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(769, 'SW & CW ', 'HE-861B', 'CW temp outlet', 'PG-8013', '2025-12-02', 2.5, 4.5, 'kg/cm²g', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(830, 'FBD-STORAGE', 'PU-103', 'Operation Pump A/B', 'Operation Pump B', NULL, NULL, NULL, NULL, 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(831, 'F-BD STORAGE', 'PU-101', 'Operation Pump A/B', 'Operation Pump B', NULL, NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(832, 'TBC NAOH', 'PU-112', 'Operation pump B/C', 'Operation Pump B', NULL, NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(833, 'SW & CW ', 'PU-815', 'Operation Pump A/B/C', 'Operation Pump B', '2025-12-02', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(834, 'SW & CW ', 'PU-815', 'Operation Pump A/B/C', 'Operation Pump C', '2025-12-02', NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(835, 'R-BD STORAGE', 'PU-111', 'Operation Pump A/B', 'Operation Pump B', NULL, NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(836, 'TBC NAOH', 'PU-112', 'Operation Pump A/C', 'Operation Pump A', NULL, NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(837, 'TBC NAOH', 'PU-112', 'Operation pump B/C', 'Operation Pump C', NULL, NULL, NULL, '', 'once/8hrs', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);

-- --------------------------------------------------------

--
-- Struktur dari tabel `sheetsatu_ignore`
--

CREATE TABLE `sheetsatu_ignore` (
  `id` int(11) NOT NULL,
  `id_sheetsatu` int(11) NOT NULL,
  `shift_ke` tinyint(4) NOT NULL,
  `waktu_ignore` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indexes for dumped tables
--

--
-- Indeks untuk tabel `login`
--
ALTER TABLE `login`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `logsheet`
--
ALTER TABLE `logsheet`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `sheetsatu`
--
ALTER TABLE `sheetsatu`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `sheetsatu_ignore`
--
ALTER TABLE `sheetsatu_ignore`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT untuk tabel yang dibuang
--

--
-- AUTO_INCREMENT untuk tabel `login`
--
ALTER TABLE `login`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT untuk tabel `logsheet`
--
ALTER TABLE `logsheet`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=22;

--
-- AUTO_INCREMENT untuk tabel `sheetsatu`
--
ALTER TABLE `sheetsatu`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=838;

--
-- AUTO_INCREMENT untuk tabel `sheetsatu_ignore`
--
ALTER TABLE `sheetsatu_ignore`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
