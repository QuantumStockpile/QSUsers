from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "roles" RENAME COLUMN "description" TO "name";
        ALTER TABLE "users" ALTER COLUMN "email" TYPE VARCHAR(255) USING "email"::VARCHAR(255);
        DROP TABLE IF EXISTS "extendedabstractmodel";
        CREATE TABLE "user_roles" (
    "role_id" INT NOT NULL REFERENCES "roles" ("id") ON DELETE CASCADE,
    "users_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
        CREATE UNIQUE INDEX "uid_users_email_133a6f" ON "users" ("email");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX "idx_users_email_133a6f";
        DROP TABLE IF EXISTS "user_roles";
        ALTER TABLE "roles" RENAME COLUMN "name" TO "description";
        ALTER TABLE "users" ALTER COLUMN "email" TYPE TEXT USING "email"::TEXT;"""
