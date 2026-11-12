package model.modeling;

import GenCol.entity;

/** Test-only envelope matching the observed DEVS-Suite 2.1 content API. */
public final class content {
    private final String portName;
    private final entity value;

    public content(String portName, entity value) {
        this.portName = portName;
        this.value = value;
    }
    public String getPortName() { return portName; }
    public entity getValue() { return value; }
}
