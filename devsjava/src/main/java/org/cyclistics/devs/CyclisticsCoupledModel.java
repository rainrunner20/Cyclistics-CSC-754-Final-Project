package org.cyclistics.devs;

import java.util.List;
import view.modeling.ViewableDigraph;

/**
 * The Cyclistics coupled DEVS network. All time values use seconds.
 *
 * Couplings route event messages. The model does NOT manually advance time:
 * the external DEVS-Suite coordinator owns the event clock.
 */
public final class CyclisticsCoupledModel extends ViewableDigraph {
    private final CyclistGenerator generator;
    private final ObstructionController obstructions;
    private final LaneBottleneck lane;

    public CyclisticsCoupledModel(String name, List<Double> arrivals,
                                 double[][] blockageWindows, double passageSeconds) {
        super(name);
        generator = new CyclistGenerator("cyclists", arrivals);
        obstructions = new ObstructionController("obstructions", blockageWindows);
        lane = new LaneBottleneck("lane", passageSeconds);

        add(generator);
        add(obstructions);
        add(lane);

        // Internal couplings: one child model's output feeds another's input.
        addCoupling(generator, "arrival", lane, "arrival");
        addCoupling(obstructions, "block", lane, "block");
        addCoupling(obstructions, "clear", lane, "clear");

        // External output coupling: expose the lane's departures from the whole model.
        addOutport("departed");
        addCoupling(lane, "departed", this, "departed");
    }

    public CyclistGenerator generator() { return generator; }
    public ObstructionController obstructions() { return obstructions; }
    public LaneBottleneck lane() { return lane; }
}
