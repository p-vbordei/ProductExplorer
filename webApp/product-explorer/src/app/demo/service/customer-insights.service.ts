import { Injectable, inject } from '@angular/core';
import { Firestore, collection, collectionData } from '@angular/fire/firestore';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class CustomerInsightsService {
  firestore: Firestore = inject(Firestore)
  customerInsights$: Observable<any[]>;

  constructor() { }

  getCustomerInsights(id) {
    this.customerInsights$ = collectionData(collection(this.firestore, 'reviewsInsights', id, 'attributeWithPercentage'));
    return this.customerInsights$;
  }
}
