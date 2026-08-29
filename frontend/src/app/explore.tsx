import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  ScrollView,
  Pressable,
  View,
  Alert,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { BottomTabInset, MaxContentWidth, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import { useLocalStories, Story } from '@/hooks/use-local-stories';

export default function ExploreScreen() {
  const safeAreaInsets = useSafeAreaInsets();
  const theme = useTheme();
  
  const insets = {
    ...safeAreaInsets,
    bottom: safeAreaInsets.bottom + BottomTabInset + Spacing.three,
  };

  const { stories, loading, deleteStory, clearAllStories, refreshStories } = useLocalStories();
  const [activeStory, setActiveStory] = useState<Story | null>(null);

  // Reload stories whenever this screen is active or refreshed
  useEffect(() => {
    refreshStories();
  }, [activeStory]);

  const handleDelete = (id: string, title: string) => {
    if (Platform.OS === 'web') {
      const confirmDelete = window.confirm(`Are you sure you want to delete "${title}"?`);
      if (confirmDelete) {
        deleteStory(id);
      }
    } else {
      Alert.alert(
        'Delete Story',
        `Are you sure you want to delete "${title}"?`,
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Delete', style: 'destructive', onPress: () => deleteStory(id) },
        ]
      );
    }
  };

  const handleClearAll = () => {
    const msg = 'Are you sure you want to delete all stories? This cannot be undone and respects your device privacy.';
    if (Platform.OS === 'web') {
      const confirmClear = window.confirm(msg);
      if (confirmClear) {
        clearAllStories();
      }
    } else {
      Alert.alert(
        'Clear Bookshelf',
        msg,
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Clear All', style: 'destructive', onPress: clearAllStories },
        ]
      );
    }
  };

  const formatDate = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return '';
    }
  };

  const contentPlatformStyle = Platform.select({
    android: {
      paddingTop: insets.top,
      paddingLeft: insets.left,
      paddingRight: insets.right,
      paddingBottom: insets.bottom,
    },
    web: {
      paddingTop: Spacing.four,
      paddingBottom: Spacing.six,
    },
  });

  // Render Full Screen Reader
  if (activeStory) {
    return (
      <ThemedView style={styles.container}>
        <ScrollView
          style={[styles.scrollView, { backgroundColor: theme.background }]}
          contentContainerStyle={[styles.contentContainer, contentPlatformStyle]}>
          <View style={styles.readerWrapper}>
            <Pressable
              style={({ pressed }) => [styles.backButton, pressed && styles.pressed]}
              onPress={() => setActiveStory(null)}>
              <ThemedText style={{ fontSize: 16 }}>← Bookshelf</ThemedText>
            </Pressable>

            <ThemedText style={styles.readerEmoji}>{activeStory.emoji}</ThemedText>
            <ThemedText type="subtitle" style={styles.readerTitle}>
              {activeStory.title}
            </ThemedText>
            
            <ThemedText type="small" themeColor="textSecondary" style={styles.readerMeta}>
              For {activeStory.age} years • Goal: {activeStory.goal}
            </ThemedText>

            <View style={styles.divider} />
            
            <ThemedText style={styles.readerStoryText}>
              {activeStory.story}
            </ThemedText>
          </View>
        </ScrollView>
      </ThemedView>
    );
  }

  // Render Bookshelf
  return (
    <ScrollView
      style={[styles.scrollView, { backgroundColor: theme.background }]}
      contentContainerStyle={[styles.contentContainer, contentPlatformStyle]}>
      <ThemedView style={styles.container}>
        
        <View style={styles.header}>
          <ThemedText type="subtitle" style={styles.headerTitle}>My Bookshelf 📚</ThemedText>
          <ThemedText themeColor="textSecondary" style={styles.headerSub}>
            All stories are kept safely on your device.
          </ThemedText>
        </View>

        {loading ? (
          <View style={styles.centerContainer}>
            <ThemedText>Opening library...</ThemedText>
          </View>
        ) : stories.length === 0 ? (
          <View style={styles.emptyContainer}>
            <ThemedText style={styles.emptyEmoji}>🍃</ThemedText>
            <ThemedText type="smallBold" style={styles.emptyText}>
              Your bookshelf is empty!
            </ThemedText>
            <ThemedText type="small" themeColor="textSecondary" style={styles.emptySubText}>
              Go to the Home tab to create a customized story based on your child's day.
            </ThemedText>
          </View>
        ) : (
          <View style={{ width: '100%', gap: Spacing.four }}>
            <View style={styles.booksGrid}>
              {stories.map((story) => (
                <View key={story.id} style={[styles.bookCard, { backgroundColor: theme.backgroundElement }]}>
                  <View style={styles.cardHeader}>
                    <ThemedText style={styles.bookEmoji}>{story.emoji}</ThemedText>
                    <ThemedText type="code" style={styles.cardDate}>
                      {formatDate(story.createdAt)}
                    </ThemedText>
                  </View>

                  <ThemedText type="smallBold" style={styles.bookTitle} numberOfLines={2}>
                    {story.title}
                  </ThemedText>

                  <ThemedText type="small" themeColor="textSecondary" style={styles.bookDesc} numberOfLines={1}>
                    {story.character} • {story.age} yrs
                  </ThemedText>

                  <View style={styles.cardActions}>
                    <Pressable
                      style={({ pressed }) => [styles.cardButton, { backgroundColor: '#4D96FF' }, pressed && styles.pressed]}
                      onPress={() => setActiveStory(story)}>
                      <ThemedText style={styles.cardButtonText}>Read 📖</ThemedText>
                    </Pressable>
                    <Pressable
                      style={({ pressed }) => [styles.cardButtonDelete, pressed && styles.pressed]}
                      onPress={() => handleDelete(story.id, story.title)}>
                      <ThemedText style={styles.deleteButtonText}>🗑️</ThemedText>
                    </Pressable>
                  </View>
                </View>
              ))}
            </View>

            <View style={styles.privacySection}>
              <View style={styles.privacyDivider} />
              <Pressable
                style={({ pressed }) => [styles.clearAllButton, pressed && styles.pressed]}
                onPress={handleClearAll}>
                <ThemedText style={styles.clearAllText}>🚨 Wipe Local Library (Privacy Clear)</ThemedText>
              </Pressable>
            </View>
          </View>
        )}

      </ThemedView>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  scrollView: {
    flex: 1,
  },
  contentContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    paddingHorizontal: Spacing.three,
  },
  container: {
    maxWidth: MaxContentWidth,
    flexGrow: 1,
    paddingTop: Spacing.three,
    alignItems: 'center',
  },
  header: {
    alignItems: 'center',
    gap: Spacing.half,
    marginBottom: Spacing.four,
  },
  headerTitle: {
    fontWeight: 'bold',
  },
  headerSub: {
    fontSize: 14,
  },
  centerContainer: {
    paddingVertical: Spacing.six,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyContainer: {
    paddingVertical: Spacing.six,
    paddingHorizontal: Spacing.four,
    alignItems: 'center',
    justifyContent: 'center',
    textAlign: 'center',
    width: '100%',
    maxWidth: 400,
    gap: Spacing.two,
  },
  emptyEmoji: {
    fontSize: 48,
    marginBottom: Spacing.one,
  },
  emptyText: {
    fontSize: 18,
    textAlign: 'center',
  },
  emptySubText: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
  booksGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.three,
    justifyContent: 'flex-start',
    width: '100%',
  },
  bookCard: {
    width: Platform.OS === 'web' ? '31%' : '47%',
    minWidth: 150,
    padding: Spacing.three,
    borderRadius: 20,
    gap: Spacing.one,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 5,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.half,
  },
  bookEmoji: {
    fontSize: 24,
  },
  cardDate: {
    fontSize: 9,
    opacity: 0.6,
  },
  bookTitle: {
    fontSize: 15,
    fontWeight: 'bold',
    height: 40,
  },
  bookDesc: {
    fontSize: 11,
    marginBottom: Spacing.half,
  },
  cardActions: {
    flexDirection: 'row',
    gap: Spacing.one,
    marginTop: Spacing.one,
  },
  cardButton: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardButtonText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: 'bold',
  },
  cardButtonDelete: {
    padding: 8,
    borderRadius: 10,
    backgroundColor: '#eaeaea',
    alignItems: 'center',
    justifyContent: 'center',
  },
  deleteButtonText: {
    fontSize: 12,
  },
  privacySection: {
    marginTop: Spacing.five,
    width: '100%',
    alignItems: 'center',
  },
  privacyDivider: {
    height: 1,
    backgroundColor: '#eaeaea',
    width: '100%',
    marginBottom: Spacing.three,
  },
  clearAllButton: {
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#FF6B6B',
  },
  clearAllText: {
    color: '#FF6B6B',
    fontSize: 12,
    fontWeight: 'bold',
  },
  readerWrapper: {
    width: '100%',
    maxWidth: 600,
    alignItems: 'center',
    paddingBottom: Spacing.six,
  },
  backButton: {
    alignSelf: 'flex-start',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    marginBottom: Spacing.three,
  },
  readerEmoji: {
    fontSize: 48,
    marginVertical: Spacing.two,
  },
  readerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: Spacing.one,
  },
  readerMeta: {
    fontSize: 13,
    marginBottom: Spacing.two,
  },
  divider: {
    height: 4,
    width: 60,
    backgroundColor: '#FF6B6B',
    borderRadius: 2,
    marginBottom: Spacing.four,
  },
  readerStoryText: {
    fontSize: 18,
    lineHeight: 28,
    textAlign: 'left',
    width: '100%',
  },
  pressed: {
    opacity: 0.8,
  },
});
