import {sqliteTable, text, integer, real, index} from "drizzle-orm/sqlite-core";
export const walletNonces = sqliteTable("wallet_nonces", {
  id: text("id").primaryKey(), wallet: text("wallet").notNull(), nonce: text("nonce").notNull(), message: text("message").notNull(), origin: text("origin").notNull(), issuedAt: integer("issued_at").notNull(), expiresAt: integer("expires_at").notNull(), consumed: integer("consumed").notNull().default(0)
}, table => [index("idx_wallet_nonces_wallet_issued").on(table.wallet, table.issuedAt)]);
export const walletSessions = sqliteTable("wallet_sessions", {tokenHash: text("token_hash").primaryKey(), wallet: text("wallet").notNull(), expiresAt: integer("expires_at").notNull()});
export const walletSnapshots = sqliteTable("wallet_snapshots", {
  id: text("id").primaryKey(), wallet: text("wallet").notNull(), ts: integer("ts").notNull(), solBalance: real("sol_balance").notNull(), valuedUsd: real("valued_usd"), complete: integer("complete").notNull(), payload: text("payload").notNull()
}, table => [index("idx_wallet_snapshots_wallet_ts").on(table.wallet, table.ts)]);
export const auditExperiments = sqliteTable("audit_experiments", {
  id: text("id").primaryKey(), owner: text("owner").notNull(), manifestJson: text("manifest_json").notNull(), manifestHash: text("manifest_hash").notNull(), status: text("status").notNull(), frozenHash: text("frozen_hash"), trainingFingerprint: text("training_fingerprint"), holdoutFingerprint: text("holdout_fingerprint"), error: text("error"), createdAt: text("created_at").notNull()
}, table => [index("idx_audit_experiments_owner_created").on(table.owner, table.createdAt)]);
export const auditEvents = sqliteTable("audit_events", {id: integer("id").primaryKey({autoIncrement:true}), experimentId: text("experiment_id").notNull().references(()=>auditExperiments.id), state: text("state").notNull(), at: text("at").notNull()});
