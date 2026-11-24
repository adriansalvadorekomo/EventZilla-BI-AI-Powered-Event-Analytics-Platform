import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', title: 'Board · EventZilla', loadComponent: () => import('./pages/board').then((m) => m.Board) },
  { path: 'revenue', title: 'Revenue · EventZilla', loadComponent: () => import('./pages/revenue').then((m) => m.Revenue) },
  { path: 'reservations', title: 'Reservations · EventZilla', loadComponent: () => import('./pages/reservations').then((m) => m.Reservations) },
  { path: 'customers', title: 'Customers · EventZilla', loadComponent: () => import('./pages/customers').then((m) => m.Customers) },
  { path: 'marketing', title: 'Marketing · EventZilla', loadComponent: () => import('./pages/marketing').then((m) => m.Marketing) },
  { path: 'quality', title: 'Data quality · EventZilla', loadComponent: () => import('./pages/quality').then((m) => m.Quality) },
  { path: '**', redirectTo: '' },
];
