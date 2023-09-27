import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { InvestigationsService } from '../../service/investigations';
import { Subscription, of  } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { LayoutService } from 'src/app/layout/service/app.layout.service';
import { MessageService } from 'primeng/api';

@Component({
  selector: 'app-investigations',
  templateUrl: './investigations.component.html',
  styleUrls: ['./investigations.component.scss']
})
export class InvestigationsComponent implements OnInit, OnDestroy {

    investiations!: any;
    newInvestigationForm: FormGroup;
    private subscriptions = new Subscription();

    constructor(
        private fb: FormBuilder, 
        private investigationsService: InvestigationsService, 
        public layoutService: LayoutService, 
        private messageService: MessageService
    ) {}

    ngOnInit() {
        this.newInvestigationForm = this.fb.group({
            name: ['', Validators.required],
            asins: ['', Validators.required]
        });
        this.initTables();
    }


    initTables() {
        const tableSub = this.investigationsService.getInvestigationCollections().subscribe((data: any) => {     
        this.investiations = data.map((entry: any) => {
            const res = {
                name: entry.name,
                asins: entry.asinList,
                investigationDate: new Date(entry.investigationDate.seconds * 1000),
                status: entry.status == "started" || entry.status == "finished" ?  entry.status : "pending",  
                id: entry.id
                } as any;
                
                return res;
            }); 
      });
      this.subscriptions.add(tableSub);
    }

    onSubmit(): void {
      if (this.newInvestigationForm.valid) {
          const formData = this.newInvestigationForm.value;
          const submitSub = this.investigationsService.postRunEndToEndInvestigation(formData.asins, formData.name).pipe(
              catchError((error) => {
                  this.messageService.add({severity:'error', summary: 'Error', detail: error.message});
                  return of(null); // Return a benign observable
              })
          ).subscribe({
              next: response => {
                  if (response) {
                      this.messageService.add({severity:'success', summary: 'Success', detail: 'Investigation started successfully!'});
                  }
              }
          });
          this.subscriptions.add(submitSub);
      } else {
          this.messageService.add({severity:'warn', summary: 'Warning', detail: 'Please fill in all required fields.'});
      }
  }

    ngOnDestroy() {
        this.subscriptions.unsubscribe();
    }

}

