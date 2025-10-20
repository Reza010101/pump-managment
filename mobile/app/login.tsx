import React, { useState } from 'react';
import { StyleSheet, TextInput, Pressable, ActivityIndicator, Platform } from 'react-native';
import { router } from 'expo-router';

import { Text, View } from '@/components/Themed';
import Colors from '@/constants/Colors';
import { apiLogin, apiGetBaseUrl } from '@/lib/api';

export default function LoginScreen() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async () => {
    setError(null);
    setLoading(true);
    try {
      const result = await apiLogin({ username, password });
      if (result.success) {
        router.replace('/(tabs)');
      } else {
        setError(result.error ?? 'ورود ناموفق بود');
      }
    } catch (e) {
      setError('خطای اتصال به سرور');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>ورود به سامانه</Text>

      <View style={styles.formGroup}>
        <Text style={styles.label}>نام کاربری</Text>
        <TextInput
          style={styles.input}
          placeholder="نام کاربری"
          value={username}
          onChangeText={setUsername}
          autoCapitalize="none"
          textContentType="username"
          returnKeyType="next"
        />
      </View>

      <View style={styles.formGroup}>
        <Text style={styles.label}>رمز عبور</Text>
        <TextInput
          style={styles.input}
          placeholder="رمز عبور"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          textContentType="password"
          returnKeyType="go"
          onSubmitEditing={onSubmit}
        />
      </View>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <Pressable style={styles.button} onPress={onSubmit} disabled={loading}>
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>ورود</Text>
        )}
      </Pressable>

      <Text style={styles.hint}>آدرس سرور: {apiGetBaseUrl()}</Text>
      <Text style={styles.hint}>
        {Platform.OS === 'android' ? 'برای امولاتور اندروید از 10.0.2.2 استفاده کنید' : ''}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
    gap: 16,
    direction: 'rtl',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    textAlign: 'center',
  },
  formGroup: {
    gap: 8,
  },
  label: {
    fontSize: 14,
    textAlign: 'right',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    textAlign: 'right',
  },
  button: {
    backgroundColor: Colors.light.tint,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  error: {
    color: '#b00020',
    textAlign: 'center',
  },
  hint: {
    marginTop: 8,
    textAlign: 'center',
    opacity: 0.7,
  },
});
