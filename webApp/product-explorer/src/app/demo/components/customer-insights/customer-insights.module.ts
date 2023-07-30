import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CustomerInsightsComponent } from './customer-insights.component';
import { ChartModule } from 'primeng/chart';
import { MenuModule } from 'primeng/menu';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { StyleClassModule } from 'primeng/styleclass';
import { PanelMenuModule } from 'primeng/panelmenu';
import { CustomerInsightsRoutingModule } from './customer-insights.-routing.module';
import { ProgressBarModule } from 'primeng/progressbar';
import { TagModule } from 'primeng/tag';


@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    ChartModule,
    MenuModule,
    TableModule,
    StyleClassModule,
    PanelMenuModule,
    ButtonModule,
    ProgressBarModule,
    TagModule,
    CustomerInsightsRoutingModule
],
declarations: [CustomerInsightsComponent]
})
export class CustomerInsightsModule { }
