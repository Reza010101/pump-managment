import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

void main() {
  runApp(const ProviderScope(child: MyApp()));
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    final baseTextTheme = GoogleFonts.vazirmatnTextTheme();
    final colorScheme = ColorScheme.fromSeed(seedColor: Colors.indigo);
    return MaterialApp(
      title: 'ژورنال روزانه',
      debugShowCheckedModeBanner: false,
      locale: const Locale('fa'),
      supportedLocales: const [
        Locale('fa'),
        Locale('en'),
      ],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: colorScheme,
        textTheme: baseTextTheme,
        appBarTheme: const AppBarTheme(centerTitle: true),
      ),
      home: const _HomeShell(),
    );
  }
}

class _HomeShell extends StatefulWidget {
  const _HomeShell({super.key});

  @override
  State<_HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<_HomeShell> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final pages = <Widget>[
      const _TodayPage(),
      const _CalendarPage(),
      const _SettingsPage(),
    ];

    final titles = <String>['امروز', 'تقویم', 'تنظیمات'];

    return Directionality(
      textDirection: TextDirection.rtl,
      child: Scaffold(
        appBar: AppBar(title: Text(titles[_index])),
        body: pages[_index],
        bottomNavigationBar: NavigationBar(
          selectedIndex: _index,
          destinations: const [
            NavigationDestination(icon: Icon(Icons.today_outlined), label: 'امروز'),
            NavigationDestination(icon: Icon(Icons.calendar_month_outlined), label: 'تقویم'),
            NavigationDestination(icon: Icon(Icons.settings_outlined), label: 'تنظیمات'),
          ],
          onDestinationSelected: (i) => setState(() => _index = i),
        ),
      ),
    );
  }
}

class _TodayPage extends StatelessWidget {
  const _TodayPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          FilledButton.icon(
            onPressed: () {},
            icon: const Icon(Icons.edit),
            label: const Text('نوشتن ژورنال امروز'),
          ),
          const SizedBox(height: 16),
          Text('کارهای امروز', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          const Expanded(
            child: Center(child: Text('لیست کارها اینجا نمایش داده می‌شود')),
          ),
        ],
      ),
    );
  }
}

class _CalendarPage extends StatelessWidget {
  const _CalendarPage({super.key});

  @override
  Widget build(BuildContext context) {
    return const Center(child: Text('تقویم شمسی (در حال ساخت)'));
  }
}

class _SettingsPage extends StatelessWidget {
  const _SettingsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return const Center(child: Text('تنظیمات (در حال ساخت)'));
  }
}
