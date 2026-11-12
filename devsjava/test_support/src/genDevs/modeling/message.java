package genDevs.modeling;

import java.util.ArrayList;
import java.util.List;
import GenCol.entity;

/** TEST-ONLY message bag. A real DEVSJAVA coordinator is still required. */
public class message {
    private final List<content> values = new ArrayList<>();
    public void add(content value) { values.add(value); }
    public int getLength() { return values.size(); }
    public String getPortName(int i) { return values.get(i).port; }
    public entity getValOnPort(String port, int index) {
        content value = values.get(index);
        return value.port.equals(port) ? value.value : null;
    }
}
