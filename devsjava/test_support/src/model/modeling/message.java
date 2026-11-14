package model.modeling;

import GenCol.entity;
import java.util.ArrayList;
import java.util.List;

/** Minimal message bag for deterministic smoke tests; NOT DEVS-Suite. */
public final class message {
    private final List<content> values = new ArrayList<>();

    public void add(content value) { values.add(value); }
    public int getLength() { return values.size(); }
    public content read(int index) { return values.get(index); }
    public boolean onPort(String portName, int index) {
        return portName.equals(read(index).getPortName());
    }
    public entity getValOnPort(String portName, int index) {
        return onPort(portName, index) ? read(index).getValue() : null;
    }
}
