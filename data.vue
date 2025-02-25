<template>
  <div class="role-management-container">
    <!-- 筛选区域：使用 el-form -->
    <el-form ref="filterForm" :model="filterData" class="filter-container" @submit.prevent="handleQuery">
      <el-form-item label="航班号" prop="flightNo">
        <el-input
          v-model="filterData.flightNo"
          placeholder="输入航班号筛选"
          clearable
          style="width: 200px;"
        />
      </el-form-item>
      <el-form-item label="集装器号" prop="uldNos">
        <el-select
          v-model="filterData.uldNos"
          multiple
          filterable
          allow-create
          default-first-option
          placeholder="输入集装器号，回车添加"
          style="width: 300px;"
        >
          <el-option
            v-for="uld in maniFest.uldList.uldTalList"
            :key="uld.uldNo"
            :label="uld.uldNo"
            :value="uld.uldNo"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="航班日期" prop="flightDateRange">
        <el-date-picker
          v-model="filterData.flightDateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 300px;"
          :default-time="[new Date(0, 0, 0, 0, 0, 0), new Date(0, 0, 0, 23, 59, 59)]"
        />
      </el-form-item>
      <el-form-item class="button-group">
        <el-button type="primary" native-type="submit">查询</el-button>
        <el-button @click="handleReset">清空</el-button>
      </el-form-item>
    </el-form>

    <!-- 数据汇总 -->
    <div class="summary-container">
      <span class="summary-item">总集装器数: {{ summaryStats.totalUlds }}</span>
      <span class="summary-item">总件数: {{ summaryStats.totalPcs }}</span>
      <span class="summary-item">总重量: {{ summaryStats.totalWt }} kg</span>
    </div>

    <!-- 主表格 -->
    <el-table
      ref="uldTable"
      :data="filteredUldList"
      :border="true"
      :row-key="row => row.uldNo"
      class="compact-table"
      style="width: 100%"
    >
      <el-table-column class="header-summary">
        <!-- 表头：显示航班信息 -->
        <template #header>
          <div class="header-content">
            <el-tooltip content="航班信息" placement="top">
              <div class="flight-info">
                <span class="info-item">航班号: {{ summaryData.flightNo }}</span>
                <span class="info-item">航班日期: {{ summaryData.flightDate }}</span>
                <span class="info-item">到达日期: {{ summaryData.arrivalDate }}</span>
              </div>
            </el-tooltip>
          </div>
        </template>

        <!-- 主行内容：集装器信息和展开控制 -->
        <template #default="props">
          <div class="row-container">
            <el-icon
              :class="['row-expand-icon', { rotate90: expandedRows.includes(props.row.uldNo) }]"
              @click="toggleRow(props.row.uldNo)"
            >
              <ArrowRight />
            </el-icon>
            <div class="uld-info">
              <span class="info-item">集装器号: {{ props.row.uldNo }}</span>
              <span class="info-item">进港时间: {{ props.row.inTime }}</span>
              <span class="info-item">目的站: {{ props.row.destination }}</span>
              <span class="info-item">件重: {{ props.row.pieceWeight }}</span>
            </div>
          </div>

          <!-- 展开内容：嵌套运单表格 -->
          <div v-if="expandedRows.includes(props.row.uldNo)" class="expanded-content">
            <el-table
              :data="props.row.talAwbList"
              :border="true"
              row-key="uldNo"
              :ref="el => tableRefItem[props.row.uldNo] = el"
              style="width: 100%"
              @row-click="rowClick"
              @selection-change="checkClick"
            >
              <el-table-column type="selection" width="55" />
              <el-table-column label="运单号" prop="awbNo" align="center" width="120">
                <template #default="scope">{{ `${scope.row.awbPre}-${scope.row.awbNo}` }}</template>
              </el-table-column>
              <el-table-column label="件数/重量" align="center" width="100">
                <template #default="scope">{{ `${scope.row.pcs}/${scope.row.wt}` }}</template>
              </el-table-column>
              <el-table-column label="目的站" prop="destStation" align="center" width="80" />
              <el-table-column label="后续航班号" prop="onwardFlightNo" align="center" width="100" />
              <el-table-column label="后续航班日期" align="center" width="120">
                <template #default="scope">{{ formatDate(scope.row.onwardFlightDate) }}</template>
              </el-table-column>
              <el-table-column label="接收集装器" prop="recieveUld" align="center" width="100" />
              <el-table-column label="接收站" prop="recievePort" align="center" width="80" />
              <el-table-column label="接收净重" prop="recieveUldNetWt" align="center" width="80" />
              <el-table-column label="接收件重" align="center" width="80">
                <template #default="scope">{{ `${scope.row.recievePcs}/${scope.row.recieveWt}` }}</template>
              </el-table-column>
              <el-table-column label="备注" prop="opeRemark" align="center" show-overflow-tooltip />
            </el-table>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted } from 'vue'
import type { ElTable, ElForm } from 'element-plus'
import { ArrowRight } from '@element-plus/icons-vue'

// 类型定义
interface Awb {
  awbPre: string
  awbNo: string
  opeRemark: string
  pcs: number
  wt: number
  destStation: string
  onwardFlightNo: string
  onwardFlightDate: Date
  recieveUld: string
  recievePort: string
  recievePcs: number
  recieveUldNetWt: number
  recieveWt: number
}

interface Uld {
  uldNo: string
  uldRemark: string
  inTime: string
  destination: string
  pieceWeight: string
  talAwbList: Awb[]
}

interface UldList {
  checkFinished: boolean
  uldTalList: Uld[]
  flightNo: string
  flightDate: string
  arrivalDate: string
}

interface Manifest {
  uldList: UldList
}

interface SummaryData {
  flightNo: string
  flightDate: string
  arrivalDate: string
}

interface SummaryStats {
  totalUlds: number
  totalPcs: number
  totalWt: number
}

interface FilterData {
  flightNo: string
  uldNos: string[]
  flightDateRange: [Date, Date] | null
}

// 数据和状态
const tableRefItem = ref<Record<string, InstanceType<typeof ElTable> | undefined>>({})
const uldTable = ref<InstanceType<typeof ElTable>>()
const filterForm = ref<InstanceType<typeof ElForm>>()
const expandedRows = ref<string[]>([])

// 默认近三天日期范围
const today = new Date()
const threeDaysAgo = new Date(today)
threeDaysAgo.setDate(today.getDate() - 2)

const filterData = ref<FilterData>({
  flightNo: '',
  uldNos: [],
  flightDateRange: [threeDaysAgo, today],
})

const maniFest = ref<Manifest>({
  uldList: {
    checkFinished: false,
    uldTalList: [
      {
        uldNo: 'ULD001',
        uldRemark: '备注1',
        inTime: '2025-02-25 10:00',
        destination: 'PEK',
        pieceWeight: '120kg',
        talAwbList: [
          {
            awbPre: 'AWB',
            awbNo: '12345678',
            opeRemark: '运单备注1',
            pcs: 50,
            wt: 60,
            destStation: 'PEK',
            onwardFlightNo: 'CA5678',
            onwardFlightDate: new Date('2025-02-26'),
            recieveUld: 'ULD001',
            recievePort: 'SHA',
            recievePcs: 48,
            recieveUldNetWt: 55,
            recieveWt: 58,
          },
          {
            awbPre: 'AWB',
            awbNo: '87654321',
            opeRemark: '运单备注2',
            pcs: 30,
            wt: 40,
            destStation: 'CAN',
            onwardFlightNo: 'CA9012',
            onwardFlightDate: new Date('2025-02-27'),
            recieveUld: 'ULD001',
            recievePort: 'CAN',
            recievePcs: 28,
            recieveUldNetWt: 35,
            recieveWt: 38,
          },
        ],
      },
      {
        uldNo: 'ULD002',
        uldRemark: '备注2',
        inTime: '2025-02-25 12:00',
        destination: 'SHA',
        pieceWeight: '85kg',
        talAwbList: [
          {
            awbPre: 'AWB',
            awbNo: '11223344',
            opeRemark: '运单备注3',
            pcs: 20,
            wt: 25,
            destStation: 'SHA',
            onwardFlightNo: 'CA3456',
            onwardFlightDate: new Date('2025-02-26'),
            recieveUld: 'ULD002',
            recievePort: 'PEK',
            recievePcs: 19,
            recieveUldNetWt: 22,
            recieveWt: 24,
          },
        ],
      },
      {
        uldNo: 'ULD003',
        uldRemark: '备注3',
        inTime: '2025-02-25 14:30',
        destination: 'CAN',
        pieceWeight: '150kg',
        talAwbList: [
          {
            awbPre: 'AWB',
            awbNo: '99887766',
            opeRemark: '运单备注4',
            pcs: 70,
            wt: 80,
            destStation: 'CAN',
            onwardFlightNo: 'CA7890',
            onwardFlightDate: new Date('2025-02-27'),
            recieveUld: 'ULD003',
            recievePort: 'SHA',
            recievePcs: 68,
            recieveUldNetWt: 75,
            recieveWt: 78,
          },
        ],
      },
    ],
    flightNo: 'CA1234',
    flightDate: '2025-02-25',
    arrivalDate: '2025-02-26',
  },
})

// 计算属性：提取航班信息
const summaryData = computed<SummaryData>(() => ({
  flightNo: maniFest.value.uldList.flightNo,
  flightDate: maniFest.value.uldList.flightDate,
  arrivalDate: maniFest.value.uldList.arrivalDate,
}))

// 计算属性：汇总统计数据
const summaryStats = computed<SummaryStats>(() => {
  const ulds = filteredUldList.value
  const totalUlds = ulds.length
  const totalPcs = ulds.reduce((sum, uld) => sum + uld.talAwbList.reduce((s, awb) => s + awb.pcs, 0), 0)
  const totalWt = ulds.reduce((sum, uld) => sum + uld.talAwbList.reduce((s, awb) => s + awb.wt, 0), 0)
  return { totalUlds, totalPcs, totalWt }
})

// 计算属性：筛选后的集装器列表
const filteredUldList = computed(() => {
  let list = maniFest.value.uldList.uldTalList
  if (filterData.value.flightNo) {
    list = list.filter(uld => maniFest.value.uldList.flightNo.includes(filterData.value.flightNo))
  }
  if (filterData.value.uldNos.length > 0) {
    list = list.filter(uld => filterData.value.uldNos.some(tag => uld.uldNo.toLowerCase().includes(tag.toLowerCase())))
  }
  if (filterData.value.flightDateRange && filterData.value.flightDateRange.length === 2) {
    const [start, end] = filterData.value.flightDateRange
    list = list.filter(uld => {
      const inTime = new Date(uld.inTime)
      return inTime >= start && inTime <= end
    })
  }
  return list
})

// 工具函数：格式化日期为 YYYY-MM-DD
const formatDate = (date: Date): string => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 方法：查询
const handleQuery = () => {
  expandedRows.value = [] // 重置展开状态
  console.log('筛选条件:', filterData.value)
}

// 方法：清空表单
const handleReset = () => {
  filterForm.value?.resetFields()
  filterData.value.uldNos = []
  filterData.value.flightDateRange = null
  expandedRows.value = []
}

// 方法：切换行展开状态
const toggleRow = (uldNo: string) => {
  const index = expandedRows.value.indexOf(uldNo)
  if (index > -1) {
    expandedRows.value.splice(index, 1)
  } else {
    expandedRows.value.push(uldNo)
  }
  console.log('当前展开的行:', expandedRows.value)
}

// 方法：处理嵌套表格行点击
const rowClick = (row: Awb) => {
  console.log('点击运单行:', row)
}

// 方法：处理选择变化
const checkClick = (selection: Awb[]) => {
  console.log('选择运单:', selection)
}

onMounted(() => {
  console.log('maniFest 数据:', maniFest.value)
  console.log('航班信息:', summaryData.value)
  console.log('汇总统计:', summaryStats.value)
})
</script>

<style scoped>
/* 容器样式 */
.role-management-container {
  padding: 20px;
  width: 100%;
  box-sizing: border-box;
}

/* 筛选区域样式 */
.filter-container {
  margin-bottom: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-start;
}

.el-form-item {
  margin-bottom: 0; /* 移除默认间距 */
}

.button-group {
  margin-left: 10px;
}

/* 数据汇总样式 */
.summary-container {
  margin-bottom: 16px;
  display: flex;
  gap: 20px;
}

.summary-item {
  padding: 6px 12px;
  background-color: #e6f7ff;
  border-radius: 6px;
  color: #1d39c4;
  font-size: 12px;
  font-weight: 500;
}

/* 表格行高调整 */
.compact-table .el-table__row {
  height: 36px;
}

/* 表头样式 */
.header-summary {
  width: 100%;
  font-size: 12px;
  overflow: hidden;
  white-space: nowrap;
}

.header-content {
  display: flex;
  align-items: center;
  padding: 0 8px;
}

.flight-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 通用信息项样式 */
.info-item {
  padding: 4px 10px;
  background-color: #f5f7fa;
  border-radius: 6px;
  color: #303133;
  font-size: 12px;
  line-height: 1.2;
}

/* 表格整体样式 */
.compact-table {
  width: 100%;
  border-radius: 4px;
  overflow: hidden;
}

/* 展开内容样式 */
.expanded-content {
  padding: 12px;
  background-color: #fafafa;
  border-top: 1px solid #e8ecef;
}

/* 行容器样式 */
.row-container {
  display: flex;
  align-items: center;
  padding: 6px 8px;
}

.uld-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 展开图标样式 */
.row-expand-icon {
  cursor: pointer;
  transition: transform 0.3s ease;
  margin-right: 10px;
  color: #606266;
}

.row-expand-icon:hover {
  color: #409eff;
}

.rotate90 {
  transform: rotate(90deg);
}

/* 嵌套表格样式 */
.expanded-content .el-table {
  font-size: 12px;
}

.expanded-content .el-table th {
  background-color: #f0f2f5;
  color: #303133;
  font-weight: 600;
}
</style>