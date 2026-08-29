import { useState, useEffect } from 'react';
import { Platform } from 'react-native';

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
}

const STORAGE_KEY = '@storyapp_saved_stories';

// Global memory cache for native platform fallback
let memoryStoriesCache: Story[] = [];

export function useLocalStories() {
  const [stories, setStories] = useState<Story[]>([]);
  const [loading, setLoading] = useState(true);

  // Helper to load stories from storage
  const loadStories = () => {
    try {
      if (Platform.OS === 'web') {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          const parsed = JSON.parse(stored) as Story[];
          setStories(parsed);
          return;
        }
      } else {
        // Native fallback using memory cache
        setStories([...memoryStoriesCache]);
        return;
      }
    } catch (e) {
      console.error('Failed to load stories:', e);
    } finally {
      setLoading(false);
    }
    setStories([]);
  };

  useEffect(() => {
    loadStories();
  }, []);

  // Save a new story
  const saveStory = async (newStoryData: {
    title: string;
    story: string;
    event: string;
    goal: string;
    character: string;
    age: string;
    emoji: string;
  }) => {
    const story: Story = {
      ...newStoryData,
      id: Math.random().toString(36).substring(2, 9) + Date.now().toString(),
      createdAt: new Date().toISOString(),
    };

    try {
      const updated = [story, ...stories];
      if (Platform.OS === 'web') {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      } else {
        memoryStoriesCache = updated;
      }
      setStories(updated);
    } catch (e) {
      console.error('Failed to save story:', e);
    }
  };

  // Delete a story
  const deleteStory = async (id: string) => {
    try {
      const updated = stories.filter((s) => s.id !== id);
      if (Platform.OS === 'web') {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      } else {
        memoryStoriesCache = updated;
      }
      setStories(updated);
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
      }
      setStories([]);
    } catch (e) {
      console.error('Failed to clear stories:', e);
    }
  };

  return {
    stories,
    loading,
    saveStory,
    deleteStory,
    clearAllStories,
    refreshStories: loadStories,
  };
}
