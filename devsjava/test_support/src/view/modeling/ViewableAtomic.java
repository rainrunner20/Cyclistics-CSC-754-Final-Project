package view.modeling;

import GenCol.entity;
import model.modeling.content;
import model.modeling.message;

/**
 * TEST-ONLY stand-in for DEVS-Suite 2.1 ViewableAtomic.
 * Do not include it in the real-JAR compilation or coordinator run.
 */
public abstract class ViewableAtomic {
    protected final String name;
    protected String phase;
    protected double sigma;

    public ViewableAtomic(String name) { this.name = name; }
    public void addInport(String portName) { }
    public void addOutport(String portName) { }
    public void initialize() { passivate(); }
    public void holdIn(String nextPhase, double timeAdvance) {
        if (timeAdvance < 0 || Double.isNaN(timeAdvance)) {
            throw new IllegalArgumentException("invalid time advance");
        }
        phase = nextPhase;
        sigma = timeAdvance;
    }
    public void passivate() { phase = "passive"; sigma = Double.POSITIVE_INFINITY; }
    public void Continue(double elapsed) {
        if (elapsed < 0 || Double.isNaN(elapsed)) {
            throw new IllegalArgumentException("invalid elapsed time");
        }
        if (Double.isFinite(sigma)) sigma = Math.max(0, sigma - elapsed);
    }
    public double ta() { return sigma; }
    public String getPhase() { return phase; }
    public abstract message out();
    public abstract void deltint();
    public abstract void deltext(double elapsed, message inputs);
    public abstract void deltcon(double elapsed, message inputs);
}
