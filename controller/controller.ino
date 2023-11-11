#include <Servo.h>
// SimpleTimeout by Thomas Feldmann 2.0.0
#include <Timeout.h>

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


#define KNIFE_L_PIN 32
#define KNIFE_R_PIN 33
#define COUNTDOWN_PIN 25

Knife lKnife(KNIFE_L_PIN, 3000, 200, 5);
Knife rKnife(KNIFE_R_PIN, 5000, 200, 180);

Countdown countdown(COUNTDOWN_PIN, 60000);

int score = 0;

void setup() {
  Serial.begin(9600);
}

void loop() {
  if (!countdown.isFinished()) {
    lKnife.update();
    rKnife.update();
    countdown.update();
  } 

  if (Serial.available() > 0) {
    String incomingData = Serial.readStringUntil('\n');
    Serial.println(incomingData);
    score = incomingData.toInt();
  }
}
 
