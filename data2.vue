<template>
  <div class="fltfdl-table-container">
    <div class="mb12" v-if="Array.isArray(opeFlightData) && opeFlightData.length > 0">
      <el-descriptions>
        <template #title>
          <span>航班信息</span>
        </template>
      </el-descriptions>
      <el-table border size="small" :data="opeFlightData" row-key="opeFlightId" scrollbar-always-on>
        <el-table-column prop="depAirportCode" fixed align="center" label="航班号">
          <template #default="{ row }">
            {{ row.carrierCode }}{{ row.flightNo }}/{{ row.flightDate }}
          </template>
        </el-table-column>
        <el-table-column prop="depAirportCode" align="center" label="出发站" />
        <el-table-column prop="arrAirportCode" align="center" label="到达站" />
        <el-table-column prop="schDepTime" align="center" label="计划起飞时间(当地)" />
        <el-table-column prop="schArrTime" align="center" label="计划到达时间(当地)" />
        <el-table-column prop="actDepTime" align="center" label="实际起飞时间" />
        <el-table-column prop="actArrTime" align="center" label="实际到达时间" />
      </el-table>
    </div>

    <div v-if="Array.isArray(tableData) && tableData.length > 0">
      <div class="header-container mb12">
        <el-descriptions>
          <template #title>
            <span>航班集装器明细</span>
          </template>
        </el-descriptions>
        <div class="radio-group">
          <el-radio v-model="flightType" label="domestic" @click.native.prevent="toggleFlightType('domestic')">
            国内
          </el-radio>
          <el-radio v-model="flightType" label="international"
            @click.native.prevent="toggleFlightType('international')">
            国际
          </el-radio>
        </div>
      </div>
      <el-card shadow="never">
        <el-table size="small" :data="tableData" :row-class-name="tableRowClassName">
          <el-table-column prop="containerNoA" align="center" label="集装器号">
            <template #default="{ row }">
              <span>{{ row.containerNoA }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="billId" align="center" label="运单号">
            <template #default="{ row }">
              <span v-if="row.containerNoA">总计：{{ row.awbCount }}</span>
              <span v-else>{{ row.billId }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="manPcs" align="center" label="件数">
            <template #default="{ row }">
              <span v-if="row.containerNoA">{{ row.pcs }}</span>
              <span v-else>{{ row.manPcs }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="manWt" align="center" label="重量">
            <template #default="{ row }">
              <span v-if="row.containerNoA">{{ row.wt }}</span>
              <span v-else>{{ row.manWt }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="destAirport" align="center" label="目的站" />
          <el-table-column prop="awbDestAirport" align="center" label="续程航班">
            <template #default="{ row }">
              <span v-if="row.containerNoA">{{}}</span>
              <span v-else>{{ row.nextCarrierCode }}{{ row.nextFlightNo }}/{{ row.nextFlightDate }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="cargoSpc" align="center" label="分拣货位/件数">
            <template #default="{ row }">
              <div v-for="(item, index) in row.talLoadList" :key="index">
                <span>
                  {{
                    item.containerNo
                      ? `${item.reloadContainerNo}/${item.pcs}`
                      : `${item.locationToName}/${item.pcs}`
                  }}
                </span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="cargoName" align="center" label="接收货位/件数">
            <template #default="{ row }">
              <div v-for="(item, index) in row.handoverLoadList" :key="index">
                <span>
                  {{
                    item.containerNo
                      ? `${item.reloadContainerNo}/${item.pcs}`
                      : `${item.locationToName}/${item.pcs}`
                  }}
                </span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="splitFlag" align="center" label="重复信息">
            <template #default="{ row }">
              <div v-for="(item, index) in row.weighList" :key="index">
                <span>
                  {{ item.containerNo }}/{{ item.uldTtlWt }}/{{ item.manTtlWt }}
                </span>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
    <el-empty v-else description="暂无数据" />
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'

// 模拟 API 返回的原始数据
const mockData = {
  data: {
    opeFlight: [
      {
        opeFlightId: '13829',
        carrierCode: 'CA',
        flightNo: '1234',
        flightDate: '2025-02-26',
        depAirportCode: 'PEK',
        arrAirportCode: 'PVG',
        schDepTime: '2025-02-26 08:00:00',
        schArrTime: '2025-02-26 10:30:00',
        actDepTime: '2025-02-26 08:05:00',
        actArrTime: '2025-02-26 10:35:00',
      },
    ],
    containerList: [
      {
        containerNo: 'AKE22402LH',
        awbCount: 1,
        pcs: 20,
        wt: 300,
        manifestList: [
          {
            billId: 'AWBA99925022406',
            manPcs: 20,
            manWt: 300,
            destAirport: 'PVG',
            nextCarrierCode: 'MU',
            nextFlightNo: '5678',
            nextFlightDate: '2025-02-26',
            talLoadList: [{ locationToName: 'A1', pcs: 20 }],
            handoverLoadList: [{ locationToName: 'B1', pcs: 20 }],
            weighList: [{ containerNo: 'AKE22402LH', uldTtlWt: 300, manTtlWt: 300 }],
          },
        ],
      },
      {
        containerNo: 'AKE22403LH',
        awbCount: 2,
        pcs: 30,
        wt: 450,
        manifestList: [
          {
            billId: 'AWBA99925022407',
            manPcs: 15,
            manWt: 225,
            destAirport: 'SHA',
            nextCarrierCode: 'CZ',
            nextFlightNo: '9101',
            nextFlightDate: '2025-02-26',
            talLoadList: [{ locationToName: 'C1', pcs: 15 }],
            handoverLoadList: [{ locationToName: 'D1', pcs: 15 }],
            weighList: [{ containerNo: 'AKE22403LH', uldTtlWt: 225, manTtlWt: 225 }],
          },
          {
            billId: 'AWBA99925022407',
            manPcs: 15,
            manWt: 225,
            destAirport: 'SHA',
            nextCarrierCode: 'CZ',
            nextFlightNo: '9101',
            nextFlightDate: '2025-02-26',
            talLoadList: [{ locationToName: 'C2', pcs: 15 }],
            handoverLoadList: [{ locationToName: 'D2', pcs: 15 }],
            weighList: [{ containerNo: 'AKE22403LH', uldTtlWt: 225, manTtlWt: 225 }],
          },
        ],
      },
      {
        containerNo: 'AKE22404LH',
        awbCount: 3,
        pcs: 45,
        wt: 600,
        manifestList: [
          {
            billId: 'AWBA99925022409',
            manPcs: 10,
            manWt: 150,
            destAirport: 'JFK',
            nextCarrierCode: 'AA',
            nextFlightNo: '1234',
            nextFlightDate: '2025-02-27',
            talLoadList: [{ locationToName: 'E1', pcs: 10 }],
            handoverLoadList: [{ locationToName: 'F1', pcs: 10 }],
            weighList: [{ containerNo: 'AKE22404LH', uldTtlWt: 150, manTtlWt: 150 }],
          },
          {
            billId: 'AWBA99925022410',
            manPcs: 20,
            manWt: 300,
            destAirport: 'LAX',
            nextCarrierCode: 'UA',
            nextFlightNo: '5678',
            nextFlightDate: '2025-02-27',
            talLoadList: [{ locationToName: 'E2', pcs: 20 }],
            handoverLoadList: [{ locationToName: 'F2', pcs: 20 }],
            weighList: [{ containerNo: 'AKE22404LH', uldTtlWt: 300, manTtlWt: 300 }],
          },
          {
            billId: 'AWBA99925022411',
            manPcs: 15,
            manWt: 150,
            destAirport: 'ORD',
            nextCarrierCode: 'DL',
            nextFlightNo: '9101',
            nextFlightDate: '2025-02-27',
            talLoadList: [{ locationToName: 'E3', pcs: 15 }],
            handoverLoadList: [{ locationToName: 'F3', pcs: 15 }],
            weighList: [{ containerNo: 'AKE22404LH', uldTtlWt: 150, manTtlWt: 150 }],
          },
        ],
      },
    ],
  },
}

const opeFlightData = ref<any[]>([])
const tableData = ref<any[]>([]) // 用于存储扁平化的表格数据
const flightType = ref('') // 默认不选中

const flightIdData = ref<any>()
const transTypeData = ref<any>()

const setData = (record: any) => {
  opeFlightData.value = record.opeFlightId ? [record] : []
  handleQuery()
}

const tableRowClassName = ({ row }: { row: any }) => {
  console.log('Row data:', row) // 调试：检查每行的数据
  if (row.containerNoA) { // 判断是否为总和行
    return 'summary-row'
  }
  return ''
}

// 模拟 getMonitorDetail API
const getMonitorDetail = async (params: any) => {
  console.log('API 参数:', params)
  return Promise.resolve(mockData) // 返回模拟数据
}

const handleQuery = async () => {
  const result = await getMonitorDetail({
    opeFlightId: flightIdData.value,
    transType: transTypeData.value,
  })
  console.log('API 返回数据:', result.data)
  if (!result || !result.data) {
    ElMessage.warning('未查询到中转数据')
    opeFlightData.value = []
    tableData.value = []
    return
  }
  opeFlightData.value = Array.isArray(result.data?.opeFlight)
    ? result.data.opeFlight
    : result.data?.opeFlight
      ? [result.data.opeFlight]
      : []

  // 组装扁平化的 tableData，根据 flightType 过滤
  tableData.value = []
  if (Array.isArray(result.data?.containerList)) {
    result.data.containerList.forEach((container: any) => {
      const isInternational = container.manifestList.some((item: any) =>
        ['JFK', 'LAX', 'ORD'].includes(item.destAirport)
      )
      const shouldInclude =
        (flightType.value === 'domestic' && !isInternational) ||
        (flightType.value === 'international' && isInternational) ||
        !flightType.value // 未选中时显示所有数据

      if (shouldInclude) {
        // 添加总和行
        tableData.value.push({
          containerNoA: container.containerNo,
          awbCount: container.awbCount,
          pcs: container.pcs,
          wt: container.wt,
        })

        // 添加 manifestList 数据，并移除 containerNo（如果存在）
        if (Array.isArray(container.manifestList)) {
          container.manifestList.forEach((item: any) => {
            const { containerNo, ...rest } = item // 移除 containerNo
            tableData.value.push(rest)
          })
        }
      }
    })
  }
  console.log('opeFlightData:', opeFlightData.value)
  console.log('tableData:', tableData.value)
}

const handleReset = () => {
  opeFlightData.value = []
  tableData.value = []
}

const toggleFlightType = (type: string) => {
  flightType.value = flightType.value === type ? '' : type
  handleQuery()
}

onMounted(() => {
  setData({
    opeFlightId: '13829',
    carrierCode: 'CA',
    flightNo: '1234',
    flightDate: '2025-02-26',
    depAirportCode: 'PEK',
    arrAirportCode: 'PVG',
    schDepTime: '2025-02-26 08:00:00',
    schArrTime: '2025-02-26 10:30:00',
    actDepTime: '2025-02-26 08:05:00',
    actArrTime: '2025-02-26 10:35:00',
  })
})

defineExpose({ setData })
</script>

<style scoped>
.mb12 {
  margin-bottom: 20px;
}

.header-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.radio-group {
  display: flex;
  gap: 10px;
}

/* 为总和行添加样式 */
.summary-row {
  background-color: #f5f7fa; /* 浅灰色背景 */
  font-weight: bold; /* 加粗文字 */
}

/* 确保样式覆盖 Element Plus 默认样式 */
:deep(.summary-row td) {
  background-color: #f5f7fa !important;
  font-weight: bold;
}



.summary-row:hover {
  background-color: #e6e8eb; /* 鼠标悬停时加深背景 */
}

:deep(.summary-row:hover td) {
  background-color: #e6e8eb !important;
}
</style>