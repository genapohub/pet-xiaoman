import { reactive, ref } from "vue";

/**
 * 列表页通用逻辑：加载态 / 分页 / 错误重试 / 搜索防抖。
 * 原先 6 个页面各自复制这套东西，加一个列表页就要再抄一遍。
 *
 * @param fetcher (query) => Promise<{items,total} | Array>
 * @param options { defaultQuery, size, immediate }
 */
export function useTable(fetcher, options = {}) {
  const { defaultQuery = {}, size = 20, immediate = true } = options;

  const rows = ref([]);
  const total = ref(0);
  const loading = ref(false);
  const failed = ref(false);
  const query = reactive({ page: 1, size, ...defaultQuery });

  async function load() {
    loading.value = true;
    failed.value = false;
    try {
      const data = await fetcher({ ...query });
      const list = Array.isArray(data) ? data : (data?.items ?? []);
      rows.value = list;
      total.value = Array.isArray(data) ? list.length : (data?.total ?? 0);
    } catch {
      // Toast 已由 request.js 统一弹出，这里只负责切到内联重试态，不重复打扰
      rows.value = [];
      total.value = 0;
      failed.value = true;
    } finally {
      loading.value = false;
    }
  }

  function setPage(page) {
    query.page = page;
    load();
  }

  function setSize(n) {
    query.size = n;
    query.page = 1;
    load();
  }

  /** 筛选条件变化：必须回第一页，否则新条件下停在第 5 页会看到空白 */
  function search() {
    query.page = 1;
    load();
  }

  let timer;
  function debouncedLoad(ms = 300) {
    clearTimeout(timer);
    timer = setTimeout(search, ms);
  }

  if (immediate) load();

  return { rows, total, loading, failed, query, load, search, setPage, setSize, debouncedLoad };
}
