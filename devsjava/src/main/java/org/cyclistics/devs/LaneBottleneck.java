package org.cyclistics.devs;

import java.util.ArrayDeque;
import java.util.Deque;

import GenCol.entity;
import genDevs.modeling.message;
import simView.ViewableAtomic;

/**
 * One-at-a-time bicycle passage with a FIFO waiting queue.
 *
 * A delivery vehicle blocks new passages, but a cyclist already passing
 * finishes the current service interval. The interval is the time needed
 * to pass this bottleneck, not the time needed for an entire bike trip.
 *
 * This class is tested with our TEST-ONLY DEVSJAVA adapter for now.
 * A real DEVSJAVA coordinator and course library are still needed.
 */
public final class LaneBottleneck extends ViewableAtomic {
    private final double passageSeconds;
    private final Deque<entity> waiting = new ArrayDeque<>();

    private entity inService;
    private boolean blocked;
    private int departed;
    private int maxWaiting;

    public LaneBottleneck(String name, double passageSeconds) {
        super(name);
        if (!Double.isFinite(passageSeconds) || passageSeconds <= 0) {
            throw new IllegalArgumentException("passageSeconds must be finite and > 0");
        }
        this.passageSeconds = passageSeconds;
        addInport("arrival");
        addInport("block");
        addInport("clear");
        addOutport("departed");
    }

    @Override
    public void initialize() {
        super.initialize();
        waiting.clear();
        inService = null;
        blocked = false;
        departed = 0;
        maxWaiting = 0;
        passivate();
    }

    @Override
    public message out() {
        // DEVS outputs are evaluated just BEFORE the internal transition.
        // The currently served cyclist leaves when their passage timer expires.
        return inService == null
                ? new message()
                : outputNameOnPort(inService.getName(), "departed");
    }

    private void finishPassage() {
        if (inService == null) {
            throw new IllegalStateException("no cyclist is currently being served");
        }
        departed++;
        inService = null;
        passivate();
    }

    private void startNextIfFree() {
        if (!blocked && inService == null && !waiting.isEmpty()) {
            inService = waiting.removeFirst();
            holdIn("serving", passageSeconds);
        }
    }

    private void applyInputs(message inputs) {
        if (inputs == null) {
            throw new IllegalArgumentException("DEVS input bag must not be null");
        }
        // Validate the entire bag before mutating state, so an invalid input
        // cannot leave half a batch of cyclists in the queue.
        for (int i = 0; i < inputs.getLength(); i++) {
            String port = inputs.getPortName(i);
            if (!"arrival".equals(port) && !"block".equals(port) && !"clear".equals(port)) {
                throw new IllegalArgumentException("unknown input port: " + port);
            }
            if ("arrival".equals(port) && inputs.getValOnPort("arrival", i) == null) {
                throw new IllegalArgumentException("arrival must identify a cyclist");
            }
        }

        // An obstruction starting and ending at the same timestamp is treated
        // conservatively: BLOCK wins, so no new passage begins on that tie.
        if (somethingOnPort(inputs, "clear")) {
            blocked = false;
        }
        if (somethingOnPort(inputs, "block")) {
            blocked = true;
        }
        for (int i = 0; i < inputs.getLength(); i++) {
            if (messageOnPort(inputs, "arrival", i)) {
                waiting.addLast(inputs.getValOnPort("arrival", i));
            }
        }
        startNextIfFree();
        maxWaiting = Math.max(maxWaiting, waiting.size());
    }

    @Override
    public void deltint() {
        // Time has advanced to a scheduled departure.
        finishPassage();
        startNextIfFree();
    }

    @Override
    public void deltext(double elapsed, message inputs) {
        // Do not restart an in-progress passage when a new cyclist or
        // blockage arrives; DEVS deducts the elapsed time from sigma.
        Continue(elapsed);
        applyInputs(inputs);
    }

    @Override
    public void deltcon(double elapsed, message inputs) {
        // At an exact tie the scheduled departure happens first.
        // Apply BLOCK/CLEAR/ARRIVAL next, then decide if another cyclist
        // can begin. This makes the simultaneous-event rule explicit.
        finishPassage();
        applyInputs(inputs);
    }

    public int waitingCount() { return waiting.size(); }
    public int departedCount() { return departed; }
    public int maxWaitingQueue() { return maxWaiting; }
    public boolean isBlocked() { return blocked; }
    public boolean isServing() { return inService != null; }
    public String currentCyclist() { return inService == null ? null : inService.getName(); }
}
