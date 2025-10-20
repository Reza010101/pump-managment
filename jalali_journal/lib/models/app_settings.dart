import 'package:isar/isar.dart';

part 'app_settings.g.dart';

@collection
class AppSettings {
  /// Use fixed id=0 for singleton settings document
  Id id = 0;

  bool journalReminderEnabled = false;
  int journalReminderHour = 21;
  int journalReminderMinute = 0;
}
