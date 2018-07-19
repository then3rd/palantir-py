/*
 Custom device configuration

 Modify grbl/config.h:
 replace:
 #define DEFAULTS_GENERIC
 with:
 #define DEFAULTS_CUSTOM

 Include DEFAULTS_CUSTOM in grbl/defaults.h below DEFAULTS_GENERIC:
 #ifdef DEFAULTS_CUSTOM
   #include "defaults/defaults_custom.h"
 #endif
*/

#ifndef defaults_h
#define defaults_h

  #define STEPS_PER_REV 200.0
  #define GEAR_RATIO 5 // 5:1 (driven:driving)
  // Dividing by 360 means that 1mm now equals 1 degree; "G91; G1 X1" rotates the driven axis by 1 degree.
  #define DEFAULT_X_STEPS_PER_MM (STEPS_PER_REV*GEAR_RATIO/360)
  #define DEFAULT_Y_STEPS_PER_MM (STEPS_PER_REV*GEAR_RATIO/360)
  #define DEFAULT_Z_STEPS_PER_MM (STEPS_PER_REV*GEAR_RATIO/360)
  #define DEFAULT_X_MAX_RATE 6000.0 // mm/min
  #define DEFAULT_Y_MAX_RATE 6000.0 // mm/min
  #define DEFAULT_Z_MAX_RATE 6000.0 // mm/min
  #define DEFAULT_X_ACCELERATION (200.0*60*60) // 10*60*60 mm/min^2 = 10 mm/sec^2
  #define DEFAULT_Y_ACCELERATION (200.0*60*60) // 10*60*60 mm/min^2 = 10 mm/sec^2
  #define DEFAULT_Z_ACCELERATION (200.0*60*60) // 10*60*60 mm/min^2 = 10 mm/sec^2
  #define DEFAULT_X_MAX_TRAVEL 360.0 // mm
  #define DEFAULT_Y_MAX_TRAVEL 360.0 // mm
  #define DEFAULT_Z_MAX_TRAVEL 360.0 // mm
  #define DEFAULT_STEP_PULSE_MICROSECONDS 10
  #define DEFAULT_STEPPING_INVERT_MASK 0
  #define DEFAULT_DIRECTION_INVERT_MASK 0
  #define DEFAULT_STEPPER_IDLE_LOCK_TIME 255 // msec (0-254, 255 keeps steppers enabled)
  #define DEFAULT_STATUS_REPORT_MASK ((BITFLAG_RT_STATUS_MACHINE_POSITION)|(BITFLAG_RT_STATUS_WORK_POSITION))
  #define DEFAULT_JUNCTION_DEVIATION 0.01 // mm
  #define DEFAULT_ARC_TOLERANCE 0.002 // mm
  #define DEFAULT_REPORT_INCHES 0 // false
  #define DEFAULT_INVERT_ST_ENABLE 0 // false
  #define DEFAULT_INVERT_LIMIT_PINS 0 // false
  #define DEFAULT_SOFT_LIMIT_ENABLE 0 // false
  #define DEFAULT_HARD_LIMIT_ENABLE 0  // false
  #define DEFAULT_HOMING_ENABLE 0  // false
  #define DEFAULT_HOMING_DIR_MASK 0 // move positive dir
  #define DEFAULT_HOMING_FEED_RATE 25.0 // mm/min
  #define DEFAULT_HOMING_SEEK_RATE 500.0 // mm/min
  #define DEFAULT_HOMING_DEBOUNCE_DELAY 250 // msec (0-65k)
  #define DEFAULT_HOMING_PULLOFF 1.0 // mm

#endif
