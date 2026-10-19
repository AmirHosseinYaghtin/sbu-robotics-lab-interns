# تقسیم کار هفتهٔ پنجم

این نسخه برای ادامهٔ کار دو نفره آماده شده است. حدود **۶۷٪ از پیاده‌سازی هفتهٔ پنجم باقی مانده** و حدود **۳۳٪ به کارهای زیر تبدیل شده است**. این نسبت، برآورد مهندسی از حجم و پیچیدگی قابلیت‌هاست؛ درصد خطوط کد یا اندازهٔ ZIP نیست. نقشه‌ها، مدل‌ها، Planner، کالیبراسیون و قابلیت‌های هفته‌های قبل در این سهم‌بندی حساب نشده‌اند.

| مسئولیت | سهم تقریبی از کار هفتهٔ پنجم |
|---|---:|
| باقی‌مانده: Action Server/Client، ارسال Goal، Feedback و Result | ۳۰٪ |
| باقی‌مانده: وضعیت داخلی Task و ترتیب اجرای موفق/ناموفق | ۱۷٪ |
| باقی‌مانده: Cancel، توقف نرم‌افزاری و تست‌های اصلی | ۲۰٪ |
| هم‌تیمی: `TODO-W5-01`، نمایش بیرونی وضعیت Task | ۱۰٪ |
| هم‌تیمی: `TODO-W5-02`، پارامترهای اجرا و سیاست تغییر زمان اجرا | ۹٪ |
| هم‌تیمی: `TODO-W5-03`، ضبط و بررسی واقعی rosbag2 | ۱۴٪ |

**`TODO-W5-01` — وضعیت Task و Monitor**

فایل‌های اصلی: `src/robot_task_system/robot_task_system/task_controller.py`، `task_monitor.py` و قرارداد موجود `src/robot_task_interfaces/srv/GetTaskStatus.srv`.

- از `self.state.snapshot()` برای پاسخ `/get_task_status` و پیام JSON روی `/task/status` استفاده کنید؛ فیلدهای قرارداد شامل `plan_file`، `task_state`، `current_action`، `action_state`، `completed_actions`، `total_actions` و `message` است.
- نقطهٔ اتصال `publish_status()` عمداً خالی است. انتشار وضعیت را در همین نقطه تکمیل کنید و نمایش Task را به Monitor برگردانید. منطق داخلی `TaskState` و تصمیم ارسال Action بعدی باقی مانده است.
- برای Topic، QoS مناسب با `RELIABLE` و `TRANSIENT_LOCAL` تعریف کنید تا مشترکی که دیر متصل می‌شود آخرین وضعیت را دریافت کند. انتشار تکراری و لاگ‌های غیرضروری را محدود کنید.
- معیار پذیرش: Service و Topic در اجرای موفق، Failure، Cancel و توقف نرم‌افزاری وضعیت یکسان و شمارندهٔ درست داشته باشند؛ پس از Failure/Cancel هیچ Action بعدی ارسال نشود؛ دلیل خطا و آخرین وضعیت برای مشترک دیرهنگام قابل مشاهده باشد.

پس از تکمیل و Build:

```bash
ros2 service call /get_task_status robot_task_interfaces/srv/GetTaskStatus '{}'
ros2 topic echo --qos-durability transient_local /task/status std_msgs/msg/String
ros2 run robot_task_system task_monitor
```

**`TODO-W5-02` — پارامترهای اجرای قابل تغییر و اعتبارسنجی**

فایل‌های اصلی: `robot_controller.py`، `task_controller.py`، `manipulator_controller.py`، `parameter_validation.py` و `src/robot_task_system/config/pick_place.yaml`.

- پارامترهای جدید اجرای Base حذف شده‌اند و کنترلر از مقادیر ثابت استفاده می‌کند: سرعت `0.15`، تلورانس‌های مسیر/پایانی/زاویه `0.10/0.02/0.03`، زمان حرکت `600`، قطع odom برابر `5`، انتظار اولیهٔ odom برابر `120` و تشخیص گیرکردن `20` ثانیه با جابه‌جایی `0.05` متر. این تنظیمات را به ROS Parameter تبدیل و همهٔ محل‌های مصرف را متصل کنید.
- مهلت‌های ثابت Task برابر `action/server/cancel = 900/120/20` ثانیه و مهلت‌های Arm برابر `arm margin/gripper/startup = 10/10/120` ثانیه است. آن‌ها نیز باید به تنظیمات معتبر و مستند تبدیل شوند.
- تنظیمات قبلی شروع برنامه، Poseهای کالیبره‌شده و مقادیر YAML حفظ شده‌اند. کنترل‌های شروع برنامه و محدودیت مفصل‌ها را نگه دارید. Guard فعلی، تغییر تنظیمات مدیریت‌شده در زمان اجرا را رد می‌کند؛ هم‌تیمی باید سیاست معتبر تغییر در `IDLE` را پیاده کند. تغییر هندسه، نام مفصل‌ها و Endpointها همچنان نیازمند Restart باشد.
- معیار پذیرش: مقدار معتبر در `IDLE` پذیرفته و واقعاً مصرف شود؛ مقدار صفر، منفی، `NaN`، `Inf` و ورودی نامعتبر در شروع برنامه و زمان اجرا به‌روشنی رد شود؛ درخواست ردشده هیچ اثر جزئی روی تنظیمات یا حرکت نگذارد؛ تغییر ناامن هنگام اجرای Action رد شود. مهلت‌ها و سرعت نهایی نیز باید از مقدار تنظیم‌شده پیروی کنند.

بدنهٔ تست‌های پذیرش پارامتر در `src/robot_task_system/test/remaining/test_parameter_acceptance.py` نگه داشته شده و فعلاً `skip` است. پس از پیاده‌سازی، Skip را بردارید، تست‌های شروع برنامه/حالت فعال را تکمیل و در مجموعهٔ تست فعال وارد کنید:

```bash
python3 -m pytest -q src/robot_task_system/test/remaining/test_parameter_acceptance.py
ros2 param set /robot_controller linear_speed 0.12
ros2 param set /robot_controller linear_speed -1.0
```

**`TODO-W5-03` — ضبط، Info و Playback واقعی rosbag2**

فایل‌های اصلی: `tools/verify_pick_place.py`، `tools/verify_bag.py` و `src/robot_task_system/config/recording_qos.yaml`. بخش‌های ضبط و Playback پیاده‌سازی نشده‌اند؛ Scaffoldهای ابزار با پیام TODO و خروج ناموفق متوقف می‌شوند. بررسی قبلی حرکت/قرارگیری جسم در شبیه‌سازی باقی مانده است.

- بعد از تکمیل `TODO-W5-01`، ضبط یک اجرای کامل را از طریق `--record-bag` پیاده کنید. Topicهای وضعیت Task، odom، TF، joint states، clock و Feedback/Status اکشن‌ها را متناسب با معماری نهایی انتخاب کنید؛ برای داده‌های سنسوری و پیام‌های ماندگار QoS مناسب تعیین کنید.
- خروجی قبلی را بازنویسی نکنید؛ Recorder را به‌درستی خاتمه دهید تا Bag نهایی شود. `ros2 bag info` و نتیجهٔ بررسی را ذخیره کنید.
- Playback را در ROS Domain جدا و بدون کنترلر ربات اجرا کنید. وجود وضعیت `COMPLETED` با شمارندهٔ کامل و پیام‌های odom/TF/joint states را بررسی کنید؛ خطا، کمبود داده یا Timeout باید خروج ناموفق بدهد.
- معیار پذیرش: یک Bag واقعی، خروجی Info، لاگ Playback و نتیجهٔ قابل بازبینی تحویل دهید. Playback مشاهدهٔ دادهٔ ثبت‌شده است و اثبات بازتولید فیزیک ربات نیست. فایل یا نتیجهٔ ساختگی جای اجرای واقعی را نمی‌گیرد.

فرمان‌های هدف پس از تکمیل ابزارها:

```bash
python3 tools/verify_pick_place.py --map simple --record-bag "$PWD/bags/week05_simple"
ros2 bag info bags/week05_simple
python3 tools/verify_bag.py bags/week05_simple
```

برای شروع، `TODO-W5-01` و `TODO-W5-02` مستقل قابل انجام‌اند؛ ضبط وضعیت Task در `TODO-W5-03` به تکمیل اولی وابسته است. قبل و بعد از تغییرات، `python3 tools/run_offline_tests.py` را اجرا کنید؛ این تست‌ها جای Build و اجرای ROS/Gazebo را نمی‌گیرند. تست‌های Cancel، Failure و توقف را فعال نگه دارید و نتیجهٔ تست‌های واقعاً اجراشده را ثبت کنید. این بسته هیچ Push به GitHub انجام نمی‌دهد.
