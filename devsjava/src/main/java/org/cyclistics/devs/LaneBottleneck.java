package org.cyclistics.devs;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import GenCol.entity;
import model.modeling.content;
import model.modeling.message;
import view.modeling.ViewableAtomic;

/**
 * One-at-a-time bicycle passage with a FIFO waiting queue.
 *
 * A delivery vehicle blocks new passages, but a cyclist already passing
 * finishes the current service interval. The interval is the time needed
 * to pass this bottleneck, not the time needed for an entire bike trip.
 *
 * Local event-time bookkeeping gives us an auditable departure trace.
 * The external DEVS coordinator still determines when to invoke transitions.
 */
public final class LaneBottleneck extends ViewableAtomic {
    private final double passageSeconds;
    private final Deque<entity> waiting = new ArrayDeque<>();

    private entity inService;
    private boolean blocked;
    private int departed;
    private int maxWaiting;
    private double logicalSeconds;
    private double scheduledDepartureSeconds;
    private final List<Departure> departures = new ArrayList<>();

    /** Immutable output record for an actual completed passage. */
    public static final class Departure {
        private final String cyclistId;
        private final double timeSeconds;

        public Departure(String cyclistId, double timeSeconds) {
            this.cyclistId = cyclistId;
            this.timeSeconds = timeSeconds;
        }
        public String cyclistId() { return cyclistId; }
        public double timeSeconds() { return timeSeconds; }
    }

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
        logicalSeconds = 0.0;
        scheduledDepartureSeconds = Double.NaN;
        departures.clear();
        passivate();
    }

    @Override
    public message out() {
        // DEVS outputs are evaluated just BEFORE the internal transition.
        // The currently served cyclist leaves when their passage timer expires.
        message output = new message();
        if (inService != null) {
            output.add(new content("departed", new entity(inService.getName())));
        }
        return output;
    }

    private void finishPassage() {
        if (inService == null) {
            throw new IllegalStateException("no cyclist is currently being served");
        }
        // The active passage's absolute completion time was fixed when it
        // started; recording it here does not depend on coordinator logging.
        if (!Double.isFinite(scheduledDepartureSeconds)
                || scheduledDepartureSeconds + 1e-9 < logicalSeconds) {
            throw new IllegalStateException("departure timer disagrees with model time");
        }
        logicalSeconds = scheduledDepartureSeconds;
        departures.add(new Departure(inService.getName(), logicalSeconds));
        departed++;
        inService = null;
        scheduledDepartureSeconds = Double.NaN;
        passivate();
    }

    private void startNextIfFree() {
        if (!blocked && inService == null && !waiting.isEmpty()) {
            inService = waiting.removeFirst();
            scheduledDepartureSeconds = logicalSeconds + passageSeconds;
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
            String port = inputs.read(i).getPortName();
            if (!"arrival".equals(port) && !"block".equals(port) && !"clear".equals(port)) {
                throw new IllegalArgumentException("unknown input port: " + port);
            }
            if ("arrival".equals(port) && inputs.getValOnPort("arrival", i) == null) {
                throw new IllegalArgumentException("arrival must identify a cyclist");
            }
        }

        // An obstruction starting and ending at the same timestamp is treated
        // conservatively: BLOCK wins, so no new passage begins on that tie.
        boolean clearReceived = false;
        boolean blockReceived = false;
        for (int i = 0; i < inputs.getLength(); i++) {
            clearReceived |= inputs.onPort("clear", i);
            blockReceived |= inputs.onPort("block", i);
        }
        if (clearReceived) {
            blocked = false;
        }
        if (blockReceived) {
            blocked = true;
        }
        for (int i = 0; i < inputs.getLength(); i++) {
            if (inputs.onPort("arrival", i)) {
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
        // The coordinator passes elapsed time since the last transition.
        // This includes time spent passivated while the lane was idle.
        logicalSeconds += elapsed;
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

    /** A read-only copy in departure order (FIFO). */
    public List<Departure> departureTrace() {
        return Collections.unmodifiableList(new ArrayList<>(departures));
    }

    public int waitingCount() { return waiting.size(); }
    public int departedCount() { return departed; }
    public int maxWaitingQueue() { return maxWaiting; }
    public boolean isBlocked() { return blocked; }
    public boolean isServing() { return inService != null; }
    public String currentCyclist() { return inService == null ? null : inService.getName(); }
}
