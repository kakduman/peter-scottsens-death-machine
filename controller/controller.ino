#include <Servo.h>
#include <Timeout.h>
#include <Stepper.h>

#define KNIFE_L_PIN 12
#define KNIFE_R_PIN 14
#define COUNTDOWN_PIN 27
#define IN1 26
#define IN2 25
#define IN3 33
#define IN4 32
#define SWITCH_PIN 15

#define TOUCH_CUTOFF 46

class Knife {
public:
  Knife(int pin, int retractedDuration, int extendedDuration, int startAngle, int endAngle) : retractedDuration(retractedDuration), extendedDuration(extendedDuration), startAngle(startAngle), endAngle(endAngle) {
    servo.attach(pin);
    servo.write(startAngle); 
    timer.start(retractedDuration);
  }

  void update() {
    if (timer.time_over()) {
      if (extended) {
        timer.start(retractedDuration);
        extended = false;
        servo.write(startAngle); 
      } else {
        timer.start(extendedDuration);
        extended = true;
        servo.write(90); 
      }
    }
  }

private:
    Servo servo;
    Timeout timer;
    bool extended = false;
    int retractedDuration;
    int extendedDuration;
    int startAngle;
    int endAngle;
};

class Countdown {
public: 
  Countdown(int pin, int totalTime) : totalTime(totalTime) {
    servo.attach(pin);
    initialize();
    moveIncrement = (int) (totalTime / 180);
  }

  void initialize() {
    finished = false;
    position = 180;
    servo.write(position); 
  }

  void update() {
    if (timer.periodic(moveIncrement)) {
      servo.write(position--);

      if (position <= endPosition) {
        timer.pause();
        timer.expire();
        finished = true;
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
    const int endPosition = 0;
    bool finished = false;
};

class FingerSwitch {
public:
  FingerSwitch(int touchPin, int touchDuration): touchPin(touchPin), touchDuration(touchDuration) {
    pinMode(touchPin, INPUT_PULLUP);
    timer.start(touchDuration);
    timer.pause();
  }

  bool switchInitiated() {
    if (touchRead(touchPin) < TOUCH_CUTOFF && !prevSwitchStatus) {
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
    if (switchInitiated()) {
      timer.start(touchDuration);
      prevSwitchStatus = true;
    }
    if (switchStatus >= TOUCH_CUTOFF && prevSwitchStatus) {
      timer.pause();
      prevSwitchStatus = false;
    }
    if (timer.time_over()) {
      timer.start(touchDuration);
      timer.pause();
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



Knife lKnife(KNIFE_L_PIN, 3000, 200, 178, 110);
Knife rKnife(KNIFE_R_PIN, 5000, 200, 0, 70);
FingerSwitch fingerSwitch(SWITCH_PIN, 3000);
Countdown countdown(COUNTDOWN_PIN, 300000);
Stepper myStepper(2048, IN1, IN3, IN2, IN4);

int score = 100;
bool gameEnd = true;

bool handleSwitch() {
  if (score < 100) {
    if (fingerSwitch.switchInitiated()) {
      myStepper.step(-128);
      return true;
    } else if (fingerSwitch.switchReleased()) {
      myStepper.step(80);
      return true;
    }
  }
  return false;
}

void initializeGame() {
  score = 0;
  gameEnd = false;
  countdown.initialize();
  Serial.println("START");
}

void setup() {
  myStepper.setSpeed(15);
  Serial.begin(9600);
  myStepper.step(32);
}

void loop() {
  if (!gameEnd) {
    if (!handleSwitch()) {
      if (countdown.isFinished()) {
        Serial.println("LOSS");
        gameEnd = true;
      }
      if (fingerSwitch.switchHeld() && score >= 100) {
        Serial.println("WIN");
        gameEnd = true;
      }
      lKnife.update();
      rKnife.update();
      countdown.update();
    }
  } else {
    if (fingerSwitch.switchHeld()) {
      initializeGame();
    }
  }
  

  if (Serial.available() > 0) {
    String incomingData = Serial.readStringUntil('\n');
    Serial.println(incomingData);
    score = incomingData.toInt();
  }
}
 
