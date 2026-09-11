import { useState, useEffect } from 'react';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface Story {
  id: string;
  title: string;
  story: string;
  event: string;
  goal: string;
  character: string;
  age: string;
  createdAt: string;
  emoji: string;
  isFavorite: boolean;
  readingProgress: number;
}

const STORAGE_KEY = '@storyapp_saved_stories';

// Global memory cache for native platform fallback
let memoryStoriesCache: Story[] = [];
const storyListeners = new Set<(stories: Story[]) => void>();

const readStories = (): Story[] => {
  try {
    if (Platform.OS === 'web') {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? normalizeStories(JSON.parse(stored)) : [];
    }
    return [...memoryStoriesCache];
  } catch (error) {
    console.error('Failed to load stories:', error);
    return [];
  }
};

async function readPersistedStories(): Promise<Story[]> {
  if (Platform.OS === 'web') return readStories();
  try {
    const stored = await AsyncStorage.getItem(STORAGE_KEY);
    const stories = stored ? normalizeStories(JSON.parse(stored)) : [];
    memoryStoriesCache = stories;
    return stories;
  } catch (error) {
    console.warn('AsyncStorage unavailable, falling back to memory:', error);
    return [...memoryStoriesCache];
  }
}

function normalizeStories(value: unknown): Story[] {
  if (!Array.isArray(value)) return [];
  return value.map((story) => ({
    ...story,
    isFavorite: story.isFavorite ?? false,
    readingProgress: story.readingProgress ?? 0,
  }));
}

async function writeStories(stories: Story[]) {
  if (Platform.OS === 'web') {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(stories));
    } catch (e) {
      console.warn('localStorage write failed:', e);
    }
  } else {
    memoryStoriesCache = stories;
    try {
      await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(stories));
    } catch (e) {
      console.warn('AsyncStorage write failed, saved in memory:', e);
    }
  }
  storyListeners.forEach((listener) => listener([...stories]));
}

function createStoryId() {
  return Math.random().toString(36).substring(2, 9) + Date.now().toString();
}

export function useLocalStories() {
  const [stories, setStories] = useState<Story[]>([]);
  const [loading, setLoading] = useState(true);

  // Helper to load stories from storage
  const loadStories = async () => {
    setStories(await readPersistedStories());
    setLoading(false);
  };

  useEffect(() => {
    void loadStories();
    storyListeners.add(setStories);
    return () => {
      storyListeners.delete(setStories);
    };
  }, []);

  // Save a new story
  const saveStory = async (newStoryData: {
    id?: string;
    createdAt?: string;
    title: string;
    story: string;
    event: string;
    goal: string;
    character: string;
    age: string;
    emoji: string;
    isFavorite?: boolean;
    readingProgress?: number;
  }): Promise<Story> => {
    const existingStories = readStories();
    const existingStory = newStoryData.id
      ? existingStories.find((story) => story.id === newStoryData.id)
      : undefined;
    const story: Story = {
      ...newStoryData,
      id: newStoryData.id ?? createStoryId(),
      createdAt: newStoryData.createdAt ?? existingStory?.createdAt ?? new Date().toISOString(),
      isFavorite: newStoryData.isFavorite ?? existingStory?.isFavorite ?? false,
      readingProgress: newStoryData.readingProgress ?? existingStory?.readingProgress ?? 0,
    };
    const withoutExisting = existingStories.filter((item) => item.id !== story.id);
    await writeStories([story, ...withoutExisting]);
    return story;
  };

  const updateStory = async (updatedStory: Story) => {
    const updated = readStories().map((story) => story.id === updatedStory.id ? updatedStory : story);
    await writeStories(updated);
    return updatedStory;
  };

  const toggleFavorite = async (id: string) => {
    const story = readStories().find((item) => item.id === id);
    if (!story) return undefined;
    return updateStory({ ...story, isFavorite: !story.isFavorite });
  };

  const getStoryById = (id: string) => readStories().find((story) => story.id === id);

  // Delete a story
  const deleteStory = async (id: string) => {
    try {
      await writeStories(readStories().filter((story) => story.id !== id));
    } catch (e) {
      console.error('Failed to delete story:', e);
    }
  };

  // Clear all stories (for privacy control)
  const clearAllStories = async () => {
    try {
      if (Platform.OS === 'web') {
        localStorage.removeItem(STORAGE_KEY);
      } else {
        memoryStoriesCache = [];
        try {
          await AsyncStorage.removeItem(STORAGE_KEY);
        } catch (e) {
          console.warn('AsyncStorage clear failed:', e);
        }
      }
      storyListeners.forEach((listener) => listener([]));
    } catch (e) {
      console.error('Failed to clear stories:', e);
    }
  };

  return {
    stories,
    loading,
    saveStory,
    updateStory,
    toggleFavorite,
    getStoryById,
    deleteStory,
    clearAllStories,
    refreshStories: loadStories,
  };
}
