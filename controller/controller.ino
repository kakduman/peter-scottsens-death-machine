#include <Servo.h>
#include <Timeout.h>
#include <Stepper.h>

class Knife {
public:
  Knife(int pin, int retractedDuration, int extendedDuration, int startAngle) : retractedDuration(retractedDuration), extendedDuration(extendedDuration), startAngle(startAngle) {
    knifeServo.attach(pin);
    knifeServo.write(startAngle); 
    knifeTimer.start(retractedDuration);
  }

  void update() {
    if (knifeTimer.time_over()) {
      if (extended) {
        knifeTimer.start(retractedDuration);
        extended = false;
        knifeServo.write(startAngle); 
      } else {
        knifeTimer.start(extendedDuration);
        extended = true;
        knifeServo.write(90); 
      }
    }
  }

private:
    Servo knifeServo;
    Timeout knifeTimer;
    bool extended = false;
    int retractedDuration;
    int extendedDuration;
    int startAngle;
};

class Countdown {
public: 
  Countdown(int pin, int totalTime) : totalTime(totalTime) {
    servo.attach(pin);
    servo.write(position); 
    moveIncrement = (int) (totalTime / 180);

  }

  void update() {
    if (timer.periodic(moveIncrement)) {
      servo.write(position--);

      if (position <= endPosition) {
        timer.pause();
        timer.expire();
        finished = true;
        Serial.println("FAIL");
      }
    }
  }

  bool isFinished() {
    return finished;
  }

  private:
    Servo servo;
    Timeout timer;
    int totalTime;
    int moveIncrement;
    int position = 180;
    int endPosition = 0;
    bool finished = false;
};

class FingerSwitch {
public:
  FingerSwitch(int touchPin, int touchDuration): touchPin(touchPin), touchDuration(touchDuration) {
    pinMode(touchPin, INPUT_PULLUP);
    timer.start(5000);
    timer.pause();
  }

  bool switchInitiated() {
    if (touchRead(touchPin) < 50 && !prevSwitchStatus) {
      prevSwitchStatus = true;
      return true;
    }
    return false;
  }
  
  bool switchReleased() {
    if (prevSwitchStatus) {
      prevSwitchStatus = false;
      return true;
    }
    return false;
  }

  bool switchHeld() {
    int switchStatus = touchRead(touchPin);
    if (switchStatus < 50 && !prevSwitchStatus) {
      timer.start(5000);
      Serial.println("started");
      prevSwitchStatus = true;
    }
    if (switchStatus >= 50 && prevSwitchStatus) {
      timer.pause();
      Serial.println("paused");
      prevSwitchStatus = false;
    }
    if (timer.time_over()) {
      timer.start(touchDuration);
      timer.pause();
      Serial.println("3 seconds");
      return true;
    }
    return false;
  }

private:
  int touchDuration;
  Timeout timer;
  int touchPin;
  bool prevSwitchStatus = false;
};

#define KNIFE_L_PIN 12
#define KNIFE_R_PIN 14
#define COUNTDOWN_PIN 27
#define IN1 26
#define IN2 25
#define IN3 33
#define IN4 32
#define SWITCH_PIN 15

Knife lKnife(KNIFE_L_PIN, 3000, 200, 5);
Knife rKnife(KNIFE_R_PIN, 5000, 200, 180);
FingerSwitch fingerSwitch(SWITCH_PIN, 3000);
Countdown countdown(COUNTDOWN_PIN, 60000);
Stepper myStepper(2048, IN1, IN3, IN2, IN4);

int score = 0;
bool gameEnd = false;

bool handleSwitch() {
  if (score < 100) {
    int switch_status = touchRead(15);
    if (fingerSwitch.switchInitiated()) {
      Serial.println("triggered");
      myStepper.step(-64);
      return true;
    } else if (fingerSwitch.switchReleased()) {
      myStepper.step(64);
      return true;
    }
  }
  return false;
}

void setup() {
  myStepper.setSpeed(15);
  Serial.begin(9600);
}

void loop() {
  if (!gameEnd) {
    if (!handleSwitch()) {
      if (!countdown.isFinished()) {
        if (fingerSwitch.switchHeld() && score >= 100) {
          Serial.println("STOP");
          gameEnd = true;
        }
        lKnife.update();
        rKnife.update();
        countdown.update();
      } 
    }
  }
  

  if (Serial.available() > 0) {
    String incomingData = Serial.readStringUntil('\n');
    Serial.println(incomingData);
    score = incomingData.toInt();
  }
}
 
