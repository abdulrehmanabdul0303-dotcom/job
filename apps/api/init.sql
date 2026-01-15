-- Reset postgres password and create database
ALTER USER postgres WITH PASSWORD 'postgres';
CREATE DATABASE IF NOT EXISTS jobpilot_dev;
