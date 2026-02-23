CREATE TABLE "items" (
  "id" integer PRIMARY KEY,
  "name" varchar,
  "category_id" integer,
  "quantity" integer,
  "status" varchar,
  "created_at" timestamp,
  "updated_at" timestamp
);

CREATE TABLE "categories" (
  "id" integer PRIMARY KEY,
  "name" varchar
);

CREATE TABLE "users" (
  "id" integer PRIMARY KEY,
  "username" varchar,
  "email" varchar,
  "password" varchar,
  "role" varchar,
  "created_at" timestamp,
  "updated_at" timestamp
);

CREATE TABLE "borrow_requests" (
  "id" integer PRIMARY KEY,
  "borrower_id" integer,
  "item_id" integer,
  "quantity" integer,
  "status" varchar,
  "verifier_id" integer,
  "borrow_date" date,
  "return_date" date,
  "created_at" timestamp,
  "updated_at" timestamp
);

CREATE TABLE "borrow_verifications" (
  "id" integer PRIMARY KEY,
  "request_id" integer,
  "verifier_id" integer,
  "status" varchar,
  "created_at" timestamp,
  "updated_at" timestamp
);

CREATE TABLE "history_logs" (
  "id" integer PRIMARY KEY,
  "action" varchar,
  "user_id" integer,
  "request_id" integer,
  "item_id" integer,
  "timestamps" timestamp,
  "previous_status" varchar,
  "new_status" varchar,
  "created_at" timestamp,
  "updated_at" timestamp
);

COMMENT ON COLUMN "items"."status" IS 'Available / Unavailable / Repairing';

ALTER TABLE "items" ADD FOREIGN KEY ("category_id") REFERENCES "categories" ("id");

ALTER TABLE "borrow_requests" ADD FOREIGN KEY ("borrower_id") REFERENCES "users" ("id");

ALTER TABLE "borrow_requests" ADD FOREIGN KEY ("item_id") REFERENCES "items" ("id");

ALTER TABLE "borrow_requests" ADD FOREIGN KEY ("verifier_id") REFERENCES "users" ("id");

ALTER TABLE "borrow_verifications" ADD FOREIGN KEY ("request_id") REFERENCES "borrow_requests" ("id");

ALTER TABLE "borrow_verifications" ADD FOREIGN KEY ("verifier_id") REFERENCES "users" ("id");

ALTER TABLE "history_logs" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "history_logs" ADD FOREIGN KEY ("request_id") REFERENCES "borrow_requests" ("id");

ALTER TABLE "history_logs" ADD FOREIGN KEY ("item_id") REFERENCES "items" ("id");

ALTER TABLE "history_logs" ADD FOREIGN KEY ("previous_status") REFERENCES "borrow_requests" ("status");

ALTER TABLE "history_logs" ADD FOREIGN KEY ("new_status") REFERENCES "borrow_requests" ("status");
