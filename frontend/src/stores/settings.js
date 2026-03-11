import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useSettingsStore = defineStore('settings', () => {
  const companyName = ref('Meine Firma')

  async function load() {
    try {
      const res = await api.get('/settings/all')
      companyName.value = res.data.company_name || 'HandOver'
    } catch {}
  }

  return { companyName, load }
})
