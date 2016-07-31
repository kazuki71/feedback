package randoop.multi;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import plume.Option;
import plume.OptionGroup;
import net.klazz.soccf.runtime.Collector;
import randoop.AbstractGenerator;
import randoop.ComponentManager;
import randoop.ExecutableSequence;
import randoop.ForwardGenerator;
import randoop.IStopper;
import randoop.ITestFilter;
import randoop.RandoopListenerManager;
import randoop.SeedSequences;
import randoop.Sequence;
import randoop.StatementKind;
import randoop.util.Randomness;
import soccf.Gateway;

public class MultiForwardGenerator extends AbstractGenerator {
  @OptionGroup(value="MultiForwardGenerator options", unpublicized=false)

  @Option("initial number of pools")
  public static int multi_init_num_pool = 10;
  @Option("maximum number of pools")
  public static int multi_max_num_pool = 100;
  @Option("randomize selectPool()")
  public static boolean multi_random_select = false;
  @Option("randomize deletePool()")
  public static boolean multi_random_delete = false;
  @Option("enable debug output")
  public static boolean multi_debug = false;
  @Option("enable warning output")
  public static boolean multi_warning = false;

  private static void debug(String s) { if (multi_debug) System.err.println(s); }
  private static void warning(String s) { if (multi_warning) System.err.println(s); }

  // fields
  public final Set<Sequence> allSequences;
  private List<Pool> pools;
  private long lastAdded;
  private long start;


  public MultiForwardGenerator(List<StatementKind> statements,
      long timeMillis, int maxSequences,
      ComponentManager componentManager,
      IStopper stopper, RandoopListenerManager listenerManager, List<ITestFilter> fs) {
    super(statements, timeMillis, maxSequences, componentManager, stopper, listenerManager, fs);
    allSequences = new LinkedHashSet<Sequence>();
    pools = new ArrayList<Pool>();

    // add initial pools
    for (int i = 0; i < multi_init_num_pool; i++) {
      pools.add(new Pool());
    }
  }

  @Override
  public int numSequences() {
    return allSequences.size();
  }

  public Set<Sequence> subsumed_sequences() {
    // dummy
    return Collections.emptySet();
  }

  public ExecutableSequence step() {
    long now = System.nanoTime();
    // set up
    if (start == 0) {
      start = now;
      lastAdded = now;
    }

    // debug print
    debug(String.format("----- %.6fs",  (now - start) / 1e9));
    for (Pool pool : pools) pool.dump();


    // add
    if (now - lastAdded > 1e9) {
      debug("trigger add");
      lastAdded = now;
      pools.add(new Pool());
    }

    // select pool
    Pool pool = selectPool(pools);
    debug("selected: " + pool.repr());

    // generate
    ExecutableSequence seq = pool.generate();

    // delete
    if (pools.size() > multi_max_num_pool) {
      debug("trigger delete");
      pools = deletePools(pools);
    }

    return seq;
  }

  Pool selectPool(List<Pool> pools) {
    Pool selected = null;
    if (multi_random_select) {
      int i = Randomness.nextRandomInt(pools.size());
      selected = pools.get(i);
    }
    else {
      double maxscore = -1.0;
      for (Pool pool: pools) {
        double score = pool.score();
        if (score > maxscore) {
          maxscore = score;
          selected = pool;
        }
      }
    }
    return selected;
  }

  List<Pool> deletePools(List<Pool> pools) {
    List<Pool> selected = new ArrayList<Pool>();
    int h = (pools.size()+1)/2; // round up
    if (multi_random_delete) {
      while (selected.size() < h) {
        int i = Randomness.nextRandomInt(pools.size());
        selected.add(pools.get(i));
        pools.remove(i);
      }
    }
    else {
      Map<Integer, Long> sums = new HashMap<Integer, Long>();
      for (Pool pool : pools) {
        Map<Integer, Long> local = pool.observer.getCoverageCounter().getBranches();
        for (int k : local.keySet()) {
          if (sums.containsKey(k)) {
            sums.put(k, sums.get(k) + local.get(k));
          }
          else {
            sums.put(k, local.get(k));
          }
        }
      }
      List<Double> uniqs = new ArrayList<Double>();
      for (Pool pool : pools) {
        Map<Integer, Long> local = pool.observer.getCoverageCounter().getBranches();
        if (local.size() == 0) {
          // new pool
          uniqs.add(Double.POSITIVE_INFINITY);
          continue;
        }
        double t = 0;
        for (int k : local.keySet()) {
          t += local.get(k) / (double)sums.get(k);
        }
        uniqs.add(t / local.size());
      }
      debug("uniqueness:");
      for (int i = 0; i < pools.size(); i++) {
        debug(String.format("%s: %.6f", pools.get(i).repr(), uniqs.get(i)));
      }
      while (selected.size() < h) {
        double maxt = -1.0;
        int maxk = -1;
        for (int i = 0; i < pools.size(); i++) {
          if (uniqs.get(i) > maxt) {
            maxt = uniqs.get(i);
            maxk = i;
          }
        }
        selected.add(pools.get(maxk));
        uniqs.set(maxk, -1.0);
      }
    }
    return selected;
  }

  private ComponentManager createComponentManager() {
    Set<Sequence> components = new LinkedHashSet<Sequence>();
    components.addAll(SeedSequences.objectsToSeeds(SeedSequences.primitiveSeeds));
    return new ComponentManager(components);
  }

  public class Pool {
    public final ForwardGenerator generator;
    public final DynamicCoverageObserver observer;
    public long time;
    public long count;

    public Pool() {
      this.generator = new ForwardGenerator(
          new ArrayList<StatementKind>(statements), maxTimeMillis, maxSequences,
          createComponentManager(), stopper, listenerMgr, outputTestFilters);
      this.observer = new DynamicCoverageObserver();
      this.time = 0;
      this.count = 0;
    }

    public ExecutableSequence generate() {
      Collector prevCollector = Gateway.getCollector();
      observer.setDestination(prevCollector);
      Gateway.setCollector(observer);
      ExecutableSequence seq;
      try {
        long start = System.nanoTime();
        seq = generator.step();
        long t = System.nanoTime() - start;
        time += t;
        count += 1;
        if (seq != null) {
          allSequences.add(seq.sequence);
          if (t > 0.5 * 1e9) warning("Long Seq:\n" + seq.sequence.toCodeString());
        }
      }
      finally {
        Gateway.setCollector(prevCollector);
        observer.setDestination(null);
      }
      dump();
      return seq;
    }

    public void dump() {
      long coverage = observer.getCoverageCounter().getBranches().size();
      debug(String.format("%s: %d [%d], %d, %.6f", repr(), count, time, coverage, score()));
    }
    
    public double score() {
      long coverage = observer.getCoverageCounter().getBranches().size();
      if (time == 0 || count == 0 || coverage == 0) return Double.POSITIVE_INFINITY;
      return coverage * 1.0e9 / time;
    }

    public String repr() {
      String s = this.toString();
      int i = s.indexOf("Pool");
      return i == -1 ? s : s.substring(i);
    }
  }
}
