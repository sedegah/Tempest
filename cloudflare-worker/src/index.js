export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(this.sweepExpiredFiles(env));
  },

  async sweepExpiredFiles(env) {
    console.log("Starting 7-day expiration sweep of R2...");
    
    const SEVEN_DAYS_MS = 7 * 24 * 60 * 60 * 1000;
    const now = Date.now();
    let truncated = false;
    let cursor = undefined;

    do {
      // List objects in the bucket
      const list = await env.BUCKET.list({ limit: 500, cursor });
      truncated = list.truncated;
      cursor = list.truncated ? list.cursor : undefined;

      for (const object of list.objects) {
        const uploadedAt = new Date(object.uploaded).getTime();
        const ageInMs = now - uploadedAt;

        if (ageInMs > SEVEN_DAYS_MS) {
          try {
            await env.BUCKET.delete(object.key);
            console.log(`Deleted expired object: ${object.key} (Age: ${Math.round(ageInMs/1000/60/60/24)} days)`);
          } catch (err) {
            console.error(`Failed to delete ${object.key}:`, err.message);
          }
        }
      }
    } while (truncated);
    
    console.log("Sweep complete.");
  }
};
