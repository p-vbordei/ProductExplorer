import { NgModule } from '@angular/core';
import { RouterModule } from '@angular/router';
import { CustomerInsightsComponent } from './customer-insights.component';
@NgModule({
    imports: [RouterModule.forChild([
        { path: '', component: CustomerInsightsComponent }
    ])],
    exports: [RouterModule]
})
export class CustomerInsightsRoutingModule { }
