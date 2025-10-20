import 'package:isar/isar.dart';

part 'journal_entry.g.dart';

@collection
class JournalEntry {
  Id id = Isar.autoIncrement;

  /// Local start of day (00:00) to ensure one entry per day
  @Index(unique: true)
  late DateTime day;

  String text = '';

  DateTime createdAt = DateTime.now();
  DateTime updatedAt = DateTime.now();
}
