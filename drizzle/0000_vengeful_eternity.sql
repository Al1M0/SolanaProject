CREATE TABLE `wallet_nonces` (
	`id` text PRIMARY KEY NOT NULL,
	`wallet` text NOT NULL,
	`nonce` text NOT NULL,
	`message` text NOT NULL,
	`origin` text NOT NULL,
	`issued_at` integer NOT NULL,
	`expires_at` integer NOT NULL,
	`consumed` integer DEFAULT 0 NOT NULL
);
--> statement-breakpoint
CREATE INDEX `idx_wallet_nonces_wallet_issued` ON `wallet_nonces` (`wallet`,`issued_at`);--> statement-breakpoint
CREATE TABLE `wallet_sessions` (
	`token_hash` text PRIMARY KEY NOT NULL,
	`wallet` text NOT NULL,
	`expires_at` integer NOT NULL
);
--> statement-breakpoint
CREATE TABLE `wallet_snapshots` (
	`id` text PRIMARY KEY NOT NULL,
	`wallet` text NOT NULL,
	`ts` integer NOT NULL,
	`sol_balance` real NOT NULL,
	`valued_usd` real,
	`complete` integer NOT NULL,
	`payload` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `idx_wallet_snapshots_wallet_ts` ON `wallet_snapshots` (`wallet`,`ts`);