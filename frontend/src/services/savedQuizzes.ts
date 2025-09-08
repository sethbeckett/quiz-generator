export interface SavedQuizSummary {
  id: number;
  topic: string;
  created_at: string;
}

const STORAGE_KEY = 'saved_quizzes_v1';

function readAll(): SavedQuizSummary[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) return parsed;
    return [];
  } catch {
    return [];
  }
}

function writeAll(items: SavedQuizSummary[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

export const SavedQuizzesStore = {
  list(): SavedQuizSummary[] { return readAll(); },
  save(summary: SavedQuizSummary): void {
    const items = readAll();
    if (!items.some(i => i.id === summary.id)) {
      items.unshift(summary);
      writeAll(items.slice(0, 200)); // limit growth
    }
  },
  remove(id: number): void {
    const items = readAll().filter(i => i.id !== id);
    writeAll(items);
  }
};



