package simView;

import GenCol.entity;
import genDevs.modeling.content;
import genDevs.modeling.message;

/**
 * TEST-ONLY minimal implementation of common DEVSJAVA method signatures.
 *
 * This is NOT the course's library and DOES NOT implement a coordinator.
 * Its only purpose is to test our atomic transition logic in isolation.
 */
public abstract class ViewableAtomic {
    protected String name;
    protected String phase;
    protected double sigma;
    public ViewableAtomic(String name) { this.name = name; }
    public void addInport(String name) {}
    public void addOutport(String name) {}
    public void initialize() { passivate(); }
    public void holdIn(String phase, double sigma) {
        if (sigma < 0) { throw new IllegalArgumentException("negative time advance"); }
        this.phase = phase; this.sigma = sigma;
    }
    public void passivate() { this.phase = "passive"; this.sigma = Double.POSITIVE_INFINITY; }
    public void Continue(double e) {
        if (e < 0) { throw new IllegalArgumentException("negative elapsed time"); }
        if (Double.isFinite(sigma)) {
            sigma = Math.max(0.0, sigma - e);
        }
    }
    public boolean somethingOnPort(message x, String port) {
        for (int i = 0; i < x.getLength(); i++) {
            if (messageOnPort(x, port, i)) { return true; }
        }
        return false;
    }
    public boolean messageOnPort(message x, String port, int index) {
        return port.equals(x.getPortName(index));
    }
    public message outputNameOnPort(String value, String port) {
        message out = new message(); out.add(new content(port, new entity(value))); return out;
    }
    public double ta() { return sigma; }
    public String getPhase() { return phase; }
    public abstract message out();
    public abstract void deltint();
    public abstract void deltext(double elapsed, message inputs);
    public abstract void deltcon(double elapsed, message inputs);
}
