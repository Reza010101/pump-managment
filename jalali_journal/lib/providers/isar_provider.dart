import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:isar/isar.dart';
import 'package:path_provider/path_provider.dart';

import '../models/app_settings.dart';
import '../models/journal_entry.dart';
import '../models/task_item.dart';

final isarProvider = FutureProvider<Isar>((ref) async {
  final dir = await getApplicationSupportDirectory();
  final isar = await Isar.open(
    [JournalEntrySchema, TaskItemSchema, AppSettingsSchema],
    directory: dir.path,
  );
  return isar;
});
