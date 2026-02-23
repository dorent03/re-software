import { createRouter, createWebHistory } from 'vue-router'
import { db } from '@/db'

const routes = [
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: 'Dashboard' },
  },
  {
    path: '/customers',
    name: 'Customers',
    component: () => import('@/views/Customers.vue'),
    meta: { title: 'Kunden' },
  },
  {
    path: '/customers/new',
    name: 'CustomerNew',
    component: () => import('@/views/CustomerEditor.vue'),
    meta: { title: 'Neuer Kunde' },
  },
  {
    path: '/customers/:id',
    name: 'CustomerEdit',
    component: () => import('@/views/CustomerEditor.vue'),
    meta: { title: 'Kunde bearbeiten' },
  },
  {
    path: '/products',
    name: 'Products',
    component: () => import('@/views/Products.vue'),
    meta: { title: 'Produkte' },
  },
  {
    path: '/products/new',
    name: 'ProductNew',
    component: () => import('@/views/ProductEditor.vue'),
    meta: { title: 'Neues Produkt' },
  },
  {
    path: '/products/:id',
    name: 'ProductEdit',
    component: () => import('@/views/ProductEditor.vue'),
    meta: { title: 'Produkt bearbeiten' },
  },
  {
    path: '/documents',
    name: 'Documents',
    component: () => import('@/views/Documents.vue'),
    meta: { title: 'Dokumente' },
  },
  {
    path: '/documents/new',
    name: 'DocumentNew',
    component: () => import('@/views/DocumentEditor.vue'),
    meta: { title: 'Neues Dokument' },
  },
  {
    path: '/documents/:id',
    name: 'DocumentEdit',
    component: () => import('@/views/DocumentEditor.vue'),
    meta: { title: 'Dokument bearbeiten' },
  },
  {
    path: '/documents/:id/pdf',
    name: 'PDFPreview',
    component: () => import('@/views/PDFPreview.vue'),
    meta: { title: 'PDF Vorschau' },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: 'Einstellungen' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  if (to.name === 'Settings') {
    next()
    return
  }
  db.company.count().then((count) => {
    if (count === 0) {
      next({ name: 'Settings' })
      return
    }
    next()
  }).catch(() => {
    next()
  })
})

export default router
