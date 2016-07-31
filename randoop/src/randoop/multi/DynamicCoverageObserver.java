package randoop.multi;

import net.klazz.soccf.runtime.Collector;
import net.klazz.soccf.runtime.CoverageCounter;

public class DynamicCoverageObserver implements Collector {
  private Collector mDestination;
  private final CoverageCounter mCounter;

  public DynamicCoverageObserver() {
    mCounter = new CoverageCounter();
  }

  public CoverageCounter getCoverageCounter() {
    return mCounter;
  }

  public synchronized void setDestination(Collector destionation) {
    mDestination = destionation;
  }

  @Override
  public synchronized void stmt(int id) {
    mCounter.stmt(id);
    if (mDestination != null) mDestination.stmt(id);
  }

  @Override
  public synchronized void branch(int id, boolean val) {
    mCounter.branch(id, val);
    if (mDestination != null) mDestination.branch(id,  val);
  }
}
