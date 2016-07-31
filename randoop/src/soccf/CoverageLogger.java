package soccf;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.FileSystem;
import java.nio.file.FileSystems;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;

import net.klazz.soccf.runtime.CoverageCounter;
import plume.Option;
import plume.OptionGroup;

public class CoverageLogger {
  @OptionGroup("CoverageLogger Options")
  @Option("directory to store log files")
  public static String log_directory = ".";
  @Option("echo coverage log to stdout")
  public static boolean log_echo_stdout = false;
  @Option("save coverage on logging")
  public static boolean log_save_coverage = false;

  public static final String COVERAGE_FILENAME = "soccf.cov.gz";
  public static final boolean COVERAGE_GZIPPED = true;
  public static final long MIN_SPAN = 100L * 1000 * 1000; // 100ms
  public static final String LOG_FILENAME = "soccf.log";

  private static BufferedWriter writer;
  private static CoverageCounter counter;
  private static long offset;
  private static long begin;
  private static long last;
  private static boolean closed;

  public static synchronized void init() {
    counter = new CoverageCounter();
    counter.readFile(log_directory + '/' + COVERAGE_FILENAME, COVERAGE_GZIPPED);
    offset = readOffset(log_directory + '/' + LOG_FILENAME);
    try {
      writer = new BufferedWriter(new FileWriter(new File(log_directory + '/' + LOG_FILENAME), true));
    }
    catch (Exception e) {
      e.printStackTrace();
    }
  }

  public static synchronized void start() {
    Gateway.setCollector(counter);
    begin = System.nanoTime();
    last = -MIN_SPAN;
    closed = false;
    Runtime.getRuntime().addShutdownHook(new Thread(new Runnable() {
      public void run() { onShutdown(); }
    }));
  }

  public static synchronized void close() {
    Gateway.setCollector(null);
    save();
    try {
      if (writer != null) {
        writer.close();
        writer = null;
      }
    }
    catch (IOException e) {
      e.printStackTrace();
    }
    closed = true;
  }

  public static synchronized void save() {
    String path = log_directory + '/' + COVERAGE_FILENAME;
    String tmpPath = getTempPath(path);
    System.out.printf("saving [%s]\n", tmpPath);
    if (counter.writeToFile(tmpPath, COVERAGE_GZIPPED)) {
      moveFile(tmpPath, path);
    }
  }

  public static synchronized void log(String comment, boolean force) {
    long now = System.nanoTime();
    if (!force && now - last < MIN_SPAN) return;
    last = now;
    StringBuilder builder = new StringBuilder();
    synchronized (soccf.Gateway.class) {
      builder.append(String.valueOf(offset + now - begin));
      builder.append(',');
      builder.append(String.valueOf(counter.getStatements().size()));
      builder.append(',');
      builder.append(String.valueOf(counter.getBranches().size()));
      builder.append(',');
      builder.append(String.valueOf(counter.getTrueBranches().size()));
      builder.append(',');
      builder.append(String.valueOf(counter.getFalseBranches().size()));
      builder.append(',');
      builder.append(comment);
    }
    String line = builder.toString();
    try {
      if (writer != null) {
        writer.write(line);
        writer.newLine();
        writer.flush();
      }
      if (log_echo_stdout) {
        System.out.println("\nSOCCF_COVERAGE_REPORT:[" + line + "]");
        System.out.flush();
      }
    }
    catch (IOException e) {
      e.printStackTrace();
    }
    if (log_save_coverage) {
      save();
    }
  }

  private static long readOffset(String filename) {
    try {
      BufferedReader reader = new BufferedReader(new FileReader(filename));
      String next, last = null;
      while ((next = reader.readLine()) != null) last = next;
      reader.close();
      if (last == null) return 0;
      return Long.valueOf(last.split(",")[0]);
    }
    catch (FileNotFoundException e) {
      return 0;
    }
    catch (Exception e) {
      e.printStackTrace();
    }
    return 0;
  }

  private static void onShutdown() {
    if (!closed) {
      log("shutdown", true);
      close();
    }
  }

  private static void moveFile(String source, String target) {
    FileSystem fs = FileSystems.getDefault();
    System.out.printf("from [%s] to [%s]\n", source, target);
    try {
      Files.move(fs.getPath(source), fs.getPath(target), StandardCopyOption.ATOMIC_MOVE);
    }
    catch (IOException e) {
      e.printStackTrace();
    }
  }

  private static String getTempPath(String path) {
    try {
      return File.createTempFile(path + ".", null).getAbsolutePath();
    }
    catch (IOException e) {
      return path + ".tmp." + System.nanoTime();
    }
  }
}
