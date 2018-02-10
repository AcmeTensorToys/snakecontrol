# Based on https://github.com/ivmech/ivPID/blob/master/PID.py
# used under GPLv3 (or later)

class PIDLoop(object):

    def __init__ (self) :
        self.kP = 0.0
        self.kPover = None
        self.kI = 0.0
        self.kD = 0.0
        self.kDDecay = 0.0
        self.smooth_error_denom = 1.0

        self.hard_max = None
        self.hard_min = None

        self.clear()

        pass

    def clear (self) :
        self.last_upd_time    = None
        self.last_error       = 0.0
        self.sum_error        = 0.0
        self.smooth_error     = 0.0

    def setKP (self, kP) :
        self.kP = kP

    def setKPover (self, kPo) :
        self.kPover = kPo

    def setKD (self, kD, kDDecay) :
        self.kD = kD
        self.kDDecay = kDDecay
        self.smooth_error_denom = 1 / (1 - kDDecay)

    def setKI (self, kI) :
        self.kI = kI

    def setPoint (self, v) :
        self.setpoint = v

    def setHardMax (self, v) :
        self.hard_max = v

    def setHardMin (self, v) :
        self.hard_min = v

    def _value (self, error, edeltasmooth) :

        # print ("PID LOOP CONTRIBUTIONS: p=%r d=%r i=%r" % (self.kP * error, self.kD * edeltasmooth, self.kI * self.sum_error))

        pterm = self.kP * error
        if (self.kPover is not None) and (error > 0) :
            pterm = self.kPover * error

        return pterm + (self.kD * edeltasmooth) + (self.kI * self.sum_error)

    def update (self, value, when) :
        if self.setpoint is None :
            raise ValueError("Setpoint not set")

        # P
        error = self.setpoint - value

        # Time
        tdelta = 0.0
        if self.last_upd_time is not None :
            tdelta = when - self.last_upd_time
        if tdelta < 0 :
            tdelta = 0.0

        # D
        edeltasmooth = 0.0
        if tdelta > 0:
            edeltasmooth = (error - (self.smooth_error/self.smooth_error_denom))/tdelta

        # I (trapezoidal integration) with optional tests against a hard stop
        ov = self._value(error, edeltasmooth)
        sum_error_delta = tdelta*(self.last_error + error)/2.0

        if self.hard_max is not None and ov >= self.hard_max and sum_error_delta > 0:
            # Do not increment error; we're already slammed up against the hard limit
            pass
        elif self.hard_min is not None and ov <= self.hard_min and sum_error_delta < 0:
            # Do not decrement error; we're already slammed up against the hard limit
            pass
        elif sum_error_delta != 0:
            # Update sum_error and recompute the output value
            self.sum_error += sum_error_delta
            ov = self._value(error, edeltasmooth)

        # Advance time
        self.last_error = error
        self.smooth_error *= self.kDDecay
        self.smooth_error += error
        self.last_upd_time = when

        return ov

    def __str__ (self) :
        return "laste=%r smoothe=%r sume=%r" % (self.last_error, self.smooth_error/self.smooth_error_denom, self.sum_error)


# A PID loop with hard limits on its behavior.  Designed as a kind of fail-safe should
# oscillations get out of hand or such.
class PIDThresh(PIDLoop):

    def __init__ (self, lowO, lowH, lowS, midO, highS, highH, highO) :
        self.low_out    = lowO
        self.low_hard   = lowH
        self.low_soft   = lowS
        self.mid_out    = midO
        self.high_soft  = highS
        self.high_hard  = highH
        self.high_out   = highO
        self.override   = None
        super(PIDThresh,self).__init__()

    def clear (self) :
        super(PIDThresh,self).clear()

    def update (self, value, when) :
        if value > self.high_hard :
            self.override = self.high_out
        elif value < self.low_hard :
            self.override = self.low_out
        elif self.override is not None and self.low_soft <= value <= self.high_soft :
            self.override = None
            super(PIDThresh,self).clear()

        if self.override : return self.override
        else : return super(PIDThresh, self).update(value,when)

    def __str__ (self) :
            return super(PIDThresh,self).__str__()
