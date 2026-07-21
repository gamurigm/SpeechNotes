import { copyFileSync, mkdirSync, rmSync } from 'node:fs';
import { join } from 'node:path';

const nextDirectory = join(process.cwd(), '.next');
const databasePath = join(nextDirectory, 'e2e.db');
const sourceDatabasePath = join(process.cwd(), 'dev.db');

mkdirSync(nextDirectory, { recursive: true });
rmSync(databasePath, { force: true });
rmSync(`${databasePath}-journal`, { force: true });
copyFileSync(sourceDatabasePath, databasePath);
