import { Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { Spacing } from '@/constants/theme';
import { useTheme, useThemeMode } from '@/hooks/use-theme';

export default function ProfileScreen() {
  const theme = useTheme();
  const { mode, toggleMode } = useThemeMode();
  const router = useRouter();

  return (
    <ThemedView style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
          <View style={styles.header}>
            <ThemedText style={styles.kicker}>YOUR SPACE</ThemedText>
            <ThemedText style={styles.title}>Profile & settings</ThemedText>
            <ThemedText themeColor="textSecondary" style={styles.subtitle}>
              Make StoryApp feel just right for your family.
            </ThemedText>
          </View>

          <View style={[styles.profileCard, { backgroundColor: theme.backgroundElement }]}>
            <View style={[styles.avatar, { backgroundColor: theme.accent }]}>
              <ThemedText themeColor="accentText" style={styles.avatarText}>✦</ThemedText>
            </View>
            <View style={styles.profileCopy}>
              <ThemedText style={styles.profileName}>Story explorer</ThemedText>
              <ThemedText type="small" themeColor="textSecondary">A quiet place for big imaginations</ThemedText>
            </View>
          </View>

          <View style={[styles.settingCard, { backgroundColor: theme.backgroundElement }]}>
            <View>
              <ThemedText style={styles.settingTitle}>App appearance</ThemedText>
              <ThemedText type="small" themeColor="textSecondary">Currently using {mode} mode</ThemedText>
            </View>
            <Pressable style={[styles.toggle, { backgroundColor: theme.backgroundSelected }]} onPress={toggleMode} accessibilityRole="switch" accessibilityState={{ checked: mode === 'dark' }}>
              <ThemedText themeColor="accent" style={styles.toggleIcon}>{mode === 'dark' ? '☾' : '☀'}</ThemedText>
              <ThemedText style={styles.toggleText}>{mode === 'dark' ? 'Dark' : 'Light'}</ThemedText>
            </Pressable>
          </View>

          <Pressable style={[styles.storiesLink, { backgroundColor: theme.accent }]} onPress={() => router.navigate('/explore')}>
            <ThemedText themeColor="accentText" style={styles.storiesLinkText}>📚 Open my stories</ThemedText>
            <ThemedText themeColor="accentText" style={styles.arrow}>→</ThemedText>
          </Pressable>
        </ScrollView>
      </SafeAreaView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  safeArea: { flex: 1, maxWidth: 440, width: '100%', alignSelf: 'center', paddingHorizontal: 20 },
  content: { paddingBottom: 120, gap: Spacing.three },
  header: { paddingTop: Spacing.four, gap: Spacing.one },
  kicker: { fontSize: 11, fontWeight: '800', letterSpacing: 1.5 },
  title: { fontSize: 32, lineHeight: 38, fontWeight: '800' },
  subtitle: { fontSize: 16, lineHeight: 23 },
  profileCard: { borderRadius: 22, padding: Spacing.three, flexDirection: 'row', alignItems: 'center', gap: Spacing.two },
  avatar: { width: 54, height: 54, borderRadius: 27, alignItems: 'center', justifyContent: 'center' },
  avatarText: { fontSize: 24 },
  profileCopy: { gap: Spacing.half },
  profileName: { fontSize: 18, fontWeight: '800' },
  settingCard: { borderRadius: 22, padding: Spacing.three, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: Spacing.two },
  settingTitle: { fontSize: 16, fontWeight: '700', marginBottom: Spacing.half },
  toggle: { minWidth: 78, minHeight: 46, borderRadius: 18, alignItems: 'center', justifyContent: 'center', flexDirection: 'row', gap: Spacing.one },
  toggleIcon: { fontSize: 18 },
  toggleText: { fontSize: 13, fontWeight: '700' },
  storiesLink: { minHeight: 56, borderRadius: 19, paddingHorizontal: Spacing.three, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  storiesLinkText: { fontSize: 16, fontWeight: '800' },
  arrow: { fontSize: 24 },
});
