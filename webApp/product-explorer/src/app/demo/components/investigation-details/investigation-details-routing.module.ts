import { NgModule } from '@angular/core';
import { RouterModule } from '@angular/router';

@NgModule({
    imports: [RouterModule.forChild([
        { path: 'customer-insights', data: { breadcrumb: 'Customer Insights' }, loadChildren: () => import('./customer-insights/customer-insights.module').then(m => m.CustomerInsightsModule) },
        { path: '**', redirectTo: '/notfound' }
    ])],
    exports: [RouterModule]
})
export class InvestigationDetailsRoutingModule { }
