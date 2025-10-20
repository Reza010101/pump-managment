import 'package:isar/isar.dart';

part 'task_item.g.dart';

@collection
class TaskItem {
  Id id = Isar.autoIncrement;

  /// Scheduled local day for the task
  @Index()
  late DateTime scheduledDay;

  late String title;
  String? description;

  /// Optional one-time reminder datetime (local)
  DateTime? reminderAt;

  bool isDone = false;

  DateTime createdAt = DateTime.now();
  DateTime updatedAt = DateTime.now();
}
