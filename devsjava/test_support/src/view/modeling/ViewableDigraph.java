package view.modeling;

import java.util.ArrayList;
import java.util.List;

/** TEST-ONLY wiring spy. This is never included in the real-JAR build. */
public class ViewableDigraph {
    private final String name;
    private final List<ViewableAtomic> children = new ArrayList<>();
    private final List<String> outputPorts = new ArrayList<>();
    private final List<String> couplings = new ArrayList<>();

    public ViewableDigraph(String name) { this.name = name; }
    public void add(ViewableAtomic model) { children.add(model); }
    public void addOutport(String port) { outputPorts.add(port); }
    public void addCoupling(Object from, String sourcePort, Object to, String targetPort) {
        couplings.add(sourcePort + "->" + targetPort);
    }
    public int childCount() { return children.size(); }
    public int couplingCount() { return couplings.size(); }
    public boolean hasOutputPort(String port) { return outputPorts.contains(port); }
    public boolean hasCoupling(String description) { return couplings.contains(description); }
    public String getName() { return name; }
}
