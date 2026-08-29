import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  ScrollView,
  TextInput,
  Pressable,
  ActivityIndicator,
  Platform,
  View,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';

import { ThemedText } from '@/components/themed-text';
import { ThemedView } from '@/components/themed-view';
import { BottomTabInset, MaxContentWidth, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import { useLocalStories } from '@/hooks/use-local-stories';

// Pre-defined values for child-friendly cards
const EVENT_PRESETS = [
  { id: 'school', title: 'First day of school', emoji: '🏫', desc: 'Starting a new class or school' },
  { id: 'tooth', title: 'Lost a tooth', emoji: '🦷', desc: 'The wiggly tooth came out' },
  { id: 'dark', title: 'Fear of the dark', emoji: '🌙', desc: 'Going to bed with lights out' },
  { id: 'sharing', title: 'Arguments over toys', emoji: '🧸', desc: 'Learning to play together' },
  { id: 'grandma', title: 'Visiting grandparent', emoji: '🏡', desc: 'A special trip to family' },
];

const GOAL_PRESETS = [
  { id: 'bravery', title: 'Bravery & Courage', emoji: '🦁', desc: 'Overcoming fears and trying new things' },
  { id: 'sharing', title: 'Sharing & Empathy', emoji: '🤝', desc: 'Understanding others and taking turns' },
  { id: 'patience', title: 'Patience & Waiting', emoji: '⏳', desc: 'Learning how to wait calmly' },
  { id: 'kindness', title: 'Kindness & Helpfulness', emoji: '❤️', desc: 'Helping friends and showing love' },
  { id: 'calmness', title: 'Calmness & Peace', emoji: '🌬️', desc: 'Taking deep breaths when angry' },
];

const CHARACTER_PRESETS = [
  { id: 'puppy', title: 'Brave Little Puppy', emoji: '🐶' },
  { id: 'astronaut', title: 'Curious Astronaut', emoji: '🚀' },
  { id: 'dragon', title: 'Friendly Dragon', emoji: '🐉' },
  { id: 'kid', title: 'Curious Child', emoji: '👦' },
];

const AGE_GROUPS = [
  { id: '3-5', label: '3-5 Years', desc: 'Cozy, simple words' },
  { id: '6-8', label: '6-8 Years', desc: 'Fun & engaging' },
  { id: '9-12', label: '9-12 Years', desc: 'Detailed stories' },
];

const LOADING_MESSAGES = [
  'Gathering magical stardust... 🌟',
  'Writing the opening chapters... 📖',
  'Adding friendly animals... 🐰',
  'Sprinkling courage and smiles... ✨',
  'Polishing the happy ending... 🎨',
];

export default function StoryMakerScreen() {
  const theme = useTheme();
  const router = useRouter();
  const { saveStory } = useLocalStories();

  // Wizard Steps:
  // 0: Welcome / Start
  // 1: Event Selection
  // 2: Goal Selection
  // 3: Age & Character Selection
  // 4: Generating / Loading
  // 5: Parent Gate / Review & Edit
  // 6: Immersive Reader
  const [step, setStep] = useState(0);

  // Form States
  const [selectedEventId, setSelectedEventId] = useState('');
  const [customEvent, setCustomEvent] = useState('');
  
  const [selectedGoalId, setSelectedGoalId] = useState('');
  
  const [selectedAge, setSelectedAge] = useState('6-8');
  const [selectedCharId, setSelectedCharId] = useState('puppy');
  const [customChar, setCustomChar] = useState('');

  // Generated Story States
  const [generatedStory, setGeneratedStory] = useState({ title: '', story: '' });
  const [loadingMessageIdx, setLoadingMessageIdx] = useState(0);
  const [apiError, setApiError] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Parent configuration
  const [backendUrl, setBackendUrl] = useState('http://localhost:8000');
  const [showConfig, setShowConfig] = useState(false);

  // Rotate loading messages
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (step === 4) {
      interval = setInterval(() => {
        setLoadingMessageIdx((prev) => (prev + 1) % LOADING_MESSAGES.length);
      }, 2500);
    }
    return () => clearInterval(interval);
  }, [step]);

  // Compute final strings for submission
  const getEventText = () => {
    if (customEvent.trim()) return customEvent.trim();
    const preset = EVENT_PRESETS.find((e) => e.id === selectedEventId);
    return preset ? preset.title : '';
  };

  const getGoalText = () => {
    const preset = GOAL_PRESETS.find((g) => g.id === selectedGoalId);
    return preset ? preset.title : 'Being Brave';
  };

  const getCharText = () => {
    if (customChar.trim()) return customChar.trim();
    const preset = CHARACTER_PRESETS.find((c) => c.id === selectedCharId);
    return preset ? preset.title : 'A brave explorer';
  };

  const getEventEmoji = () => {
    const preset = EVENT_PRESETS.find((e) => e.id === selectedEventId);
    return preset ? preset.emoji : '✨';
  };

  // Submit request to FastAPI
  const handleGenerate = async () => {
    const eventText = getEventText();
    if (!eventText) {
      alert('Please select or write a daily event!');
      return;
    }
    if (!selectedGoalId) {
      alert('Please select a story goal focus!');
      return;
    }

    setApiError('');
    setStep(4); // Move to Loading step

    try {
      const response = await fetch(`${backendUrl}/generate-story`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          age: selectedAge,
          event: eventText,
          goal: getGoalText(),
          character: getCharText(),
          language: 'English',
        }),
      });

      if (!response.ok) {
        throw new Error(`Server returned error: ${response.status}`);
      }

      const data = await response.json();
      setGeneratedStory({
        title: data.title || 'A Magical Adventure',
        story: data.story || 'Once upon a time...',
      });
      setSaveSuccess(false);
      setStep(5); // Move to Parent Gate Review
    } catch (error: any) {
      console.error(error);
      setApiError(
        `Failed to reach the story engine. Is the backend server running at ${backendUrl}?`
      );
      setStep(3); // Return to previous step
    }
  };

  // Save reviewed story
  const handleSave = async () => {
    setIsSaving(true);
    try {
      await saveStory({
        title: generatedStory.title,
        story: generatedStory.story,
        event: getEventText(),
        goal: getGoalText(),
        character: getCharText(),
        age: selectedAge,
        emoji: getEventEmoji(),
      });
      setSaveSuccess(true);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSaving(false);
    }
  };

  // Step Navigations
  const handleNextStep = () => {
    if (step === 1 && !getEventText()) {
      alert('Please choose or write an event first!');
      return;
    }
    if (step === 2 && !selectedGoalId) {
      alert('Please select a story goal first!');
      return;
    }
    setStep((prev) => prev + 1);
  };

  const handlePrevStep = () => {
    setStep((prev) => prev - 1);
  };

  const handleReset = () => {
    setSelectedEventId('');
    setCustomEvent('');
    setSelectedGoalId('');
    setSelectedCharId('puppy');
    setCustomChar('');
    setSaveSuccess(false);
    setStep(0);
  };

  // Render Functions for Steps
  const renderWelcome = () => (
    <View style={styles.cardContainer}>
      <ThemedView type="backgroundElement" style={styles.introCard}>
        <ThemedText style={styles.emojiHero}>🦄 🚀 🐶 🐉</ThemedText>
        <ThemedText type="title" style={styles.mainTitle}>
          StoryLand
        </ThemedText>
        <ThemedText type="subtitle" style={styles.subText}>
          Create magical tales tailored to your child's day!
        </ThemedText>
        <ThemedText style={styles.explanationText} themeColor="textSecondary">
          A privacy-focused, kid-friendly way to turn everyday events like lost teeth or school nervousness into therapeutic adventures.
        </ThemedText>

        <Pressable
          style={({ pressed }) => [
            styles.primaryButton,
            pressed && styles.pressed,
            { backgroundColor: '#FF6B6B' },
          ]}
          onPress={() => setStep(1)}>
          <ThemedText style={styles.primaryButtonText}>Start Adventure ✨</ThemedText>
        </Pressable>

        <Pressable
          style={styles.configToggle}
          onPress={() => setShowConfig(!showConfig)}>
          <ThemedText type="small" themeColor="textSecondary">
            ⚙️ Server Settings
          </ThemedText>
        </Pressable>

        {showConfig && (
          <View style={styles.configBox}>
            <ThemedText type="smallBold">FastAPI Backend URL:</ThemedText>
            <TextInput
              style={[styles.textInput, { color: theme.text, borderColor: theme.backgroundSelected }]}
              value={backendUrl}
              onChangeText={setBackendUrl}
              placeholder="http://localhost:8000"
            />
            <ThemedText type="code" style={{ fontSize: 10 }}>
              (Change this to your local IP address, e.g. http://192.168.1.50:8000 if testing on a phone)
            </ThemedText>
          </View>
        )}
      </ThemedView>
    </View>
  );

  const renderEventStep = () => (
    <View style={styles.stepWrapper}>
      <ThemedText type="subtitle" style={styles.stepHeader}>
        Step 1: What happened today? ☀️
      </ThemedText>
      <ThemedText themeColor="textSecondary" style={styles.stepSub}>
        Choose a daily event or write a custom experience to inspire the story.
      </ThemedText>

      <ScrollView contentContainerStyle={styles.presetsGrid} style={{ maxHeight: 320 }}>
        {EVENT_PRESETS.map((preset) => {
          const isSelected = selectedEventId === preset.id && !customEvent;
          return (
            <Pressable
              key={preset.id}
              style={[
                styles.presetCard,
                { backgroundColor: theme.backgroundElement },
                isSelected && { borderColor: '#4D96FF', borderWidth: 2, backgroundColor: theme.backgroundSelected },
              ]}
              onPress={() => {
                setSelectedEventId(preset.id);
                setCustomEvent('');
              }}>
              <ThemedText style={styles.presetEmoji}>{preset.emoji}</ThemedText>
              <View style={styles.presetTextCol}>
                <ThemedText type="smallBold">{preset.title}</ThemedText>
                <ThemedText type="small" themeColor="textSecondary">
                  {preset.desc}
                </ThemedText>
              </View>
            </Pressable>
          );
        })}
      </ScrollView>

      <View style={styles.customInputContainer}>
        <ThemedText type="smallBold" style={styles.inputLabel}>
          Or describe a specific event:
        </ThemedText>
        <TextInput
          style={[
            styles.textAreaInput,
            {
              color: theme.text,
              backgroundColor: theme.backgroundElement,
              borderColor: theme.backgroundSelected,
            },
          ]}
          multiline
          numberOfLines={3}
          value={customEvent}
          onChangeText={(text) => {
            setCustomEvent(text);
            setSelectedEventId('');
          }}
          placeholder="e.g. Maya fell off her scooter today but got right back up and smiled."
          placeholderTextColor={theme.textSecondary}
        />
      </View>

      <View style={styles.navRow}>
        <Pressable
          style={[styles.secondaryButton, { borderColor: theme.textSecondary }]}
          onPress={handlePrevStep}>
          <ThemedText>Back</ThemedText>
        </Pressable>
        <Pressable
          style={[styles.primaryButton, { backgroundColor: '#4D96FF' }]}
          onPress={handleNextStep}>
          <ThemedText style={styles.primaryButtonText}>Next: Choose Goal ➔</ThemedText>
        </Pressable>
      </View>
    </View>
  );

  const renderGoalStep = () => (
    <View style={styles.stepWrapper}>
      <ThemedText type="subtitle" style={styles.stepHeader}>
        Step 2: Story Theme & Goal 🌟
      </ThemedText>
      <ThemedText themeColor="textSecondary" style={styles.stepSub}>
        What positive growth focus should the character explore?
      </ThemedText>

      <ScrollView contentContainerStyle={styles.presetsGrid} style={{ maxHeight: 320 }}>
        {GOAL_PRESETS.map((preset) => {
          const isSelected = selectedGoalId === preset.id;
          return (
            <Pressable
              key={preset.id}
              style={[
                styles.presetCard,
                { backgroundColor: theme.backgroundElement },
                isSelected && { borderColor: '#6BCB77', borderWidth: 2, backgroundColor: theme.backgroundSelected },
              ]}
              onPress={() => setSelectedGoalId(preset.id)}>
              <ThemedText style={styles.presetEmoji}>{preset.emoji}</ThemedText>
              <View style={styles.presetTextCol}>
                <ThemedText type="smallBold">{preset.title}</ThemedText>
                <ThemedText type="small" themeColor="textSecondary">
                  {preset.desc}
                </ThemedText>
              </View>
            </Pressable>
          );
        })}
      </ScrollView>

      <View style={styles.navRow}>
        <Pressable
          style={[styles.secondaryButton, { borderColor: theme.textSecondary }]}
          onPress={handlePrevStep}>
          <ThemedText>Back</ThemedText>
        </Pressable>
        <Pressable
          style={[styles.primaryButton, { backgroundColor: '#6BCB77' }]}
          onPress={handleNextStep}>
          <ThemedText style={styles.primaryButtonText}>Next: Character ➔</ThemedText>
        </Pressable>
      </View>
    </View>
  );

  const renderCharStep = () => (
    <View style={styles.stepWrapper}>
      <ThemedText type="subtitle" style={styles.stepHeader}>
        Step 3: Age & Character 🐶
      </ThemedText>
      <ThemedText themeColor="textSecondary" style={styles.stepSub}>
        Customize the hero and story length for your child.
      </ThemedText>

      {apiError ? (
        <ThemedView type="backgroundElement" style={styles.errorBanner}>
          <ThemedText style={{ color: '#FF6B6B', fontSize: 13 }}>⚠️ {apiError}</ThemedText>
        </ThemedView>
      ) : null}

      <ThemedText type="smallBold" style={styles.inputLabel}>
        Select Age Group (Story style & length):
      </ThemedText>
      <View style={styles.ageButtonGroup}>
        {AGE_GROUPS.map((grp) => {
          const isSelected = selectedAge === grp.id;
          return (
            <Pressable
              key={grp.id}
              style={[
                styles.ageButton,
                { backgroundColor: theme.backgroundElement },
                isSelected && { backgroundColor: '#FFA1A1', borderColor: '#FF6B6B', borderWidth: 1 },
              ]}
              onPress={() => setSelectedAge(grp.id)}>
              <ThemedText type="smallBold">{grp.label}</ThemedText>
              <ThemedText type="code" style={{ fontSize: 9 }}>
                {grp.desc}
              </ThemedText>
            </Pressable>
          );
        })}
      </View>

      <ThemedText type="smallBold" style={[styles.inputLabel, { marginTop: Spacing.three }]}>
        Choose Main Character Hero:
      </ThemedText>
      <View style={styles.charGrid}>
        {CHARACTER_PRESETS.map((preset) => {
          const isSelected = selectedCharId === preset.id && !customChar;
          return (
            <Pressable
              key={preset.id}
              style={[
                styles.charCard,
                { backgroundColor: theme.backgroundElement },
                isSelected && { borderColor: '#4D96FF', borderWidth: 2, backgroundColor: theme.backgroundSelected },
              ]}
              onPress={() => {
                setSelectedCharId(preset.id);
                setCustomChar('');
              }}>
              <ThemedText style={styles.charEmoji}>{preset.emoji}</ThemedText>
              <ThemedText type="smallBold" style={{ fontSize: 12 }}>
                {preset.title}
              </ThemedText>
            </Pressable>
          );
        })}
      </View>

      <View style={styles.customInputContainer}>
        <ThemedText type="smallBold" style={styles.inputLabel}>
          Or write custom character description:
        </ThemedText>
        <TextInput
          style={[
            styles.textInput,
            {
              color: theme.text,
              backgroundColor: theme.backgroundElement,
              borderColor: theme.backgroundSelected,
            },
          ]}
          value={customChar}
          onChangeText={(text) => {
            setCustomChar(text);
            setSelectedCharId('');
          }}
          placeholder="e.g. A sleepy hedgehog named Pip who wears tiny red boots"
          placeholderTextColor={theme.textSecondary}
        />
      </View>

      <View style={styles.navRow}>
        <Pressable
          style={[styles.secondaryButton, { borderColor: theme.textSecondary }]}
          onPress={handlePrevStep}>
          <ThemedText>Back</ThemedText>
        </Pressable>
        <Pressable
          style={[styles.primaryButton, { backgroundColor: '#FFA1A1' }]}
          onPress={handleGenerate}>
          <ThemedText style={styles.primaryButtonText}>✨ Generate Story! ✨</ThemedText>
        </Pressable>
      </View>
    </View>
  );

  const renderGenerating = () => (
    <View style={styles.cardContainer}>
      <ThemedView type="backgroundElement" style={styles.loadingCard}>
        <ActivityIndicator size="large" color="#FF6B6B" style={{ marginBottom: Spacing.four }} />
        <ThemedText type="subtitle" style={styles.loadingHeader}>
          Creating Magic...
        </ThemedText>
        <ThemedText style={styles.loadingText}>
          {LOADING_MESSAGES[loadingMessageIdx]}
        </ThemedText>
        <ThemedText type="small" themeColor="textSecondary" style={{ marginTop: Spacing.five, textAlign: 'center' }}>
          Rest easy. Your details are only sent to the local generation server.
        </ThemedText>
      </ThemedView>
    </View>
  );

  const renderParentGate = () => (
    <View style={styles.stepWrapper}>
      <View style={styles.parentGateHeader}>
        <ThemedText type="subtitle">🔒 Parent Review Panel</ThemedText>
        <ThemedText type="small" themeColor="textSecondary">
          Review, personalize, and edit the story before reading it to your child.
        </ThemedText>
      </View>

      <ScrollView style={styles.editScroll} contentContainerStyle={{ gap: Spacing.two }}>
        <ThemedText type="smallBold">Story Title:</ThemedText>
        <TextInput
          style={[
            styles.textInput,
            {
              color: theme.text,
              backgroundColor: theme.backgroundElement,
              borderColor: theme.backgroundSelected,
              fontWeight: 'bold',
            },
          ]}
          value={generatedStory.title}
          onChangeText={(text) => setGeneratedStory((prev) => ({ ...prev, title: text }))}
        />

        <ThemedText type="smallBold" style={{ marginTop: Spacing.two }}>
          Story Content:
        </ThemedText>
        <TextInput
          style={[
            styles.editTextArea,
            {
              color: theme.text,
              backgroundColor: theme.backgroundElement,
              borderColor: theme.backgroundSelected,
              fontSize: 15,
              lineHeight: 22,
            },
          ]}
          multiline
          value={generatedStory.story}
          onChangeText={(text) => setGeneratedStory((prev) => ({ ...prev, story: text }))}
        />
      </ScrollView>

      <View style={styles.navRow}>
        <Pressable
          style={[
            styles.secondaryButton,
            { borderColor: saveSuccess ? '#6BCB77' : theme.textSecondary },
          ]}
          onPress={handleSave}
          disabled={isSaving}>
          <ThemedText style={saveSuccess ? { color: '#6BCB77' } : undefined}>
            {isSaving ? 'Saving...' : saveSuccess ? '✓ Saved!' : 'Save Story 💾'}
          </ThemedText>
        </Pressable>
        <Pressable
          style={[styles.primaryButton, { backgroundColor: '#FF6B6B' }]}
          onPress={() => setStep(6)}>
          <ThemedText style={styles.primaryButtonText}>Read with Child 📖</ThemedText>
        </Pressable>
      </View>
    </View>
  );

  const renderFinalStory = () => (
    <View style={styles.readerWrapper}>
      <ScrollView contentContainerStyle={styles.readerContent}>
        <ThemedText style={styles.readerEmoji}>{getEventEmoji()}</ThemedText>
        <ThemedText type="subtitle" style={styles.readerTitle}>
          {generatedStory.title}
        </ThemedText>
        
        <View style={styles.divider} />
        
        <ThemedText style={styles.readerStoryText}>
          {generatedStory.story}
        </ThemedText>
      </ScrollView>

      <View style={styles.readerNavRow}>
        <Pressable
          style={[styles.secondaryButton, { borderColor: theme.text }]}
          onPress={handleReset}>
          <ThemedText>New Story 🔄</ThemedText>
        </Pressable>
        <Pressable
          style={[styles.primaryButton, { backgroundColor: '#4D96FF' }]}
          onPress={() => {
            router.navigate('/explore');
            handleReset();
          }}>
          <ThemedText style={styles.primaryButtonText}>Bookshelf 📚</ThemedText>
        </Pressable>
      </View>
    </View>
  );

  // Return the main container
  return (
    <ThemedView style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        {step === 0 && renderWelcome()}
        {step === 1 && renderEventStep()}
        {step === 2 && renderGoalStep()}
        {step === 3 && renderCharStep()}
        {step === 4 && renderGenerating()}
        {step === 5 && renderParentGate()}
        {step === 6 && renderFinalStory()}
      </SafeAreaView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    flexDirection: 'row',
  },
  safeArea: {
    flex: 1,
    paddingHorizontal: Spacing.three,
    maxWidth: MaxContentWidth,
    justifyContent: 'center',
    paddingBottom: BottomTabInset + Spacing.two,
  },
  cardContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  introCard: {
    padding: Spacing.four,
    borderRadius: 24,
    width: '100%',
    maxWidth: 500,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 5,
  },
  emojiHero: {
    fontSize: 48,
    marginBottom: Spacing.two,
  },
  mainTitle: {
    fontFamily: Platform.OS === 'ios' ? 'ui-rounded' : 'sans-serif',
    fontSize: 40,
    fontWeight: 'bold',
    color: '#FF6B6B',
    textAlign: 'center',
    marginBottom: Spacing.one,
  },
  subText: {
    fontSize: 18,
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: Spacing.three,
  },
  explanationText: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: Spacing.four,
  },
  primaryButton: {
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'stretch',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.15,
    shadowRadius: 5,
    elevation: 3,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: 'bold',
  },
  secondaryButton: {
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 16,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
  },
  configToggle: {
    marginTop: Spacing.four,
    padding: Spacing.one,
  },
  configBox: {
    marginTop: Spacing.two,
    alignSelf: 'stretch',
    gap: Spacing.one,
  },
  textInput: {
    borderWidth: 1,
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 14,
    fontSize: 14,
    alignSelf: 'stretch',
  },
  textAreaInput: {
    borderWidth: 1,
    borderRadius: 12,
    paddingVertical: 10,
    paddingHorizontal: 14,
    fontSize: 14,
    alignSelf: 'stretch',
    textAlignVertical: 'top',
    height: 80,
  },
  stepWrapper: {
    flex: 1,
    justifyContent: 'flex-start',
    paddingTop: Spacing.two,
    gap: Spacing.three,
  },
  stepHeader: {
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: Spacing.half,
  },
  stepSub: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: Spacing.one,
  },
  presetsGrid: {
    gap: Spacing.two,
    paddingRight: Spacing.one,
  },
  presetCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: Spacing.three,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'transparent',
    marginBottom: Spacing.one,
  },
  presetEmoji: {
    fontSize: 28,
    marginRight: Spacing.three,
  },
  presetTextCol: {
    flex: 1,
  },
  customInputContainer: {
    gap: Spacing.one,
    marginTop: Spacing.one,
  },
  inputLabel: {
    fontSize: 14,
  },
  navRow: {
    flexDirection: 'row',
    gap: Spacing.two,
    marginTop: 'auto',
    paddingVertical: Spacing.two,
  },
  errorBanner: {
    padding: Spacing.two,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#FF6B6B',
  },
  ageButtonGroup: {
    flexDirection: 'row',
    gap: Spacing.two,
    alignSelf: 'stretch',
  },
  ageButton: {
    flex: 1,
    paddingVertical: Spacing.two,
    alignItems: 'center',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  charGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.two,
  },
  charCard: {
    width: '47%',
    flexDirection: 'row',
    alignItems: 'center',
    padding: Spacing.two,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'transparent',
    gap: Spacing.two,
  },
  charEmoji: {
    fontSize: 24,
  },
  loadingCard: {
    padding: Spacing.five,
    borderRadius: 24,
    width: '100%',
    maxWidth: 400,
    alignItems: 'center',
  },
  loadingHeader: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: Spacing.two,
  },
  loadingText: {
    fontSize: 16,
    textAlign: 'center',
    color: '#FF6B6B',
    fontWeight: 'bold',
  },
  parentGateHeader: {
    gap: Spacing.half,
    marginBottom: Spacing.two,
  },
  editScroll: {
    flex: 1,
    marginBottom: Spacing.two,
  },
  editTextArea: {
    borderWidth: 1,
    borderRadius: 12,
    padding: Spacing.three,
    textAlignVertical: 'top',
    height: 350,
  },
  readerWrapper: {
    flex: 1,
    paddingTop: Spacing.two,
  },
  readerContent: {
    alignItems: 'center',
    paddingBottom: Spacing.six,
  },
  readerEmoji: {
    fontSize: 48,
    marginVertical: Spacing.two,
  },
  readerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
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
  readerNavRow: {
    flexDirection: 'row',
    gap: Spacing.two,
    paddingVertical: Spacing.two,
    borderTopWidth: 1,
    borderColor: '#eaeaea',
  },
  pressed: {
    opacity: 0.85,
    transform: [{ scale: 0.98 }],
  },
});
