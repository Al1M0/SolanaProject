CREATE TABLE `audit_events` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`experiment_id` text NOT NULL,
	`state` text NOT NULL,
	`at` text NOT NULL,
	FOREIGN KEY (`experiment_id`) REFERENCES `audit_experiments`(`id`) ON UPDATE no action ON DELETE no action
);
--> statement-breakpoint
CREATE TABLE `audit_experiments` (
	`id` text PRIMARY KEY NOT NULL,
	`owner` text NOT NULL,
	`manifest_json` text NOT NULL,
	`manifest_hash` text NOT NULL,
	`status` text NOT NULL,
	`frozen_hash` text,
	`training_fingerprint` text,
	`holdout_fingerprint` text,
	`error` text,
	`created_at` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `idx_audit_experiments_owner_created` ON `audit_experiments` (`owner`,`created_at`);--> statement-breakpoint
CREATE TRIGGER audit_manifest_immutable BEFORE UPDATE OF id, owner, manifest_json, manifest_hash ON audit_experiments BEGIN SELECT RAISE(ABORT, 'Experiment snapshot is immutable'); END;
--> statement-breakpoint
CREATE TRIGGER audit_frozen_immutable BEFORE UPDATE OF frozen_hash ON audit_experiments WHEN OLD.frozen_hash IS NOT NULL AND NEW.frozen_hash IS NOT OLD.frozen_hash BEGIN SELECT RAISE(ABORT, 'Frozen hash is immutable'); END;
