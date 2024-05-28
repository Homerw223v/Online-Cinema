CREATE DATABASE IF NOT EXISTS shard_1;

CREATE TABLE IF NOT EXISTS shard_1.metrics (
    user_id UUID,
    timestamp DateTime,
    url String,
    action String,
    information String
  )
  Engine=ReplicatedMergeTree('/clickhouse/tables/{shard_1}/{database}/metrics', '{replica_name}')
  PARTITION BY toYYYYMMDD(timestamp) ORDER BY timestamp;

CREATE TABLE IF NOT EXISTS default.metrics (
    user_id UUID,
    timestamp DateTime,
    url String,
    action String,
    information String
  )
  ENGINE = Distributed('company_cluster', '', metrics, rand());

CREATE DATABASE IF NOT EXISTS shard_2;

CREATE TABLE IF NOT EXISTS shard_2.metrics (
    user_id UUID,
    timestamp DateTime,
    url String,
    action String,
    information String
  )
  Engine=ReplicatedMergeTree('/clickhouse/tables/{shard_2}/{database}/metrics', '{replica_name}')
  PARTITION BY toYYYYMMDD(timestamp) ORDER BY timestamp;

CREATE DATABASE IF NOT EXISTS shard_3;

CREATE TABLE IF NOT EXISTS shard_3.metrics (
    user_id UUID,
    timestamp DateTime,
    url String,
    action String,
    information String
  )
  Engine=ReplicatedMergeTree('/clickhouse/tables/{shard_3}/{database}/metrics', '{replica_name}')
  PARTITION BY toYYYYMMDD(timestamp) ORDER BY timestamp;